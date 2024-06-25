const mongoose = require('mongoose');
const autoIncrement = require('mongoose-auto-increment');

// Initialize auto-increment
autoIncrement.initialize(mongoose.connection)

const UrlSchema = new mongoose.Schema({
  originalUrl: { type: String, required: true },
  shortUrl: { type: Number, required: true, unique: true },
  createdAt: { type: Date, default: Date.now }
});

UrlSchema.plugin(autoIncrement.plugin, {
  model: 'Url',
  field: 'shortUrl',
  startAt: 1,
  incrementBy: 1
});

module.exports = mongoose.model('Url', UrlSchema);
