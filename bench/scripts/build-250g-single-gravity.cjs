'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { GravityModel } = require('../../host/arm-control/GravityModel');
const base = require('../config/so101-two-joint-controller.json');

const [, , input, outputDir] = process.argv;
if (!input || !outputDir) throw Error('Usage: node build-250g-single-gravity.cjs INPUT.json NEW_OUTPUT_DIRECTORY');
const data = JSON.parse(fs.readFileSync(input, 'utf8').replace(/^\uFEFF/, ''));

function measurement(key, min, max) {
  const value = data[key];
  if (!Number.isFinite(value) || value < min || value > max) throw Error('Missing or invalid measurement: ' + key);
  return value;
}

const id = measurement('motorId', 1, 253);
if (!Number.isInteger(id) || typeof data.port !== 'string' || !data.port.trim()) throw Error('Set a valid motor ID and port');
const zero = measurement('horizontalCounts', 0, 4095);
const direction = data.direction;
if (direction !== 1 && direction !== -1) throw Error('Set direction to +1 if increasing counts lifts the horizontal arm, or -1 otherwise');
const pwmPerNm = measurement('pwmPerNm', 0.001, 100000);
const mass = measurement('massKg', 0.001, 10);
const center = measurement('centerMm', 0.001, 1000);
const peakTorqueNm = 9.80665 * mass * center / 1000;
const weight = direction * 2 * Math.PI / 4096;
const profiles = { [id]: base.profiles[1] };
const document = {
  format: 'sts-gravity', version: 1, units: 'pwm-effort',
  name: 'Single STS3215 with a bench load',
  calibration: 'Horizontal encoder reference, measured lift direction and calibrated effort per Nm.',
  mounting: 'Horizontal shaft with the bench load carried by the servo horn.',
  payload: mass + ' kg at a radius of ' + center + ' mm.',
  encoderCalibration: { [id]: data.encoderCalibration },
  models: { [id]: {
    maxEffort: profiles[id].effortLimit,
    note: 'Single-axis static gravity moment, highest with the hanger horizontal.',
    terms: [{ fn: 'cos', weights: { [id]: weight }, offsetRad: -weight * zero, coefficient: direction * peakTorqueNm * pwmPerNm }],
  } },
};
const model = new GravityModel(document);
model.validateIds([id]);
const peakEffort = model.evaluate({ [id]: zero }, [id], profiles)[id];
const gravityModel = 'gravity-250g-single-model.json';
const controller = { ...base, followerPort: data.port, joints: [{ followerId: id }], profiles, gravityModel };
fs.mkdirSync(outputDir);
for (const [name, content] of [[gravityModel, document], ['gravity-250g-single-controller.json', controller]]) {
  fs.writeFileSync(path.join(outputDir, name), JSON.stringify(content, null, 2) + '\n');
}
console.log({ peakTorqueNm, peakEffort });
