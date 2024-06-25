const mongoose = require('mongoose');

const CounterSchema = new mongoose.Schema({
  count: { type: Number, default: 1 }
});

module.exports = mongoose.model('Counter', CounterSchema);
