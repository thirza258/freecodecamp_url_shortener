require('dotenv').config();
const express = require('express');
const cors = require('cors');
const app = express();
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const dns = require('dns');
const shortid = require('shortid');
const {URL} = require('url');
const Url = require('./Url');
const autoIncrement = require('mongoose-auto-increment');

// Basic Configuration
const port = process.env.PORT || 3000;
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
//URL schema

app.use(cors());

app.use('/public', express.static(`${process.cwd()}/public`));

app.get('/', function(req, res) {
  res.sendFile(process.cwd() + '/views/index.html');
});

mongoose.connect(process.env.MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
}).then(() => console.log('MongoDB connected...'))
  .catch(err => console.log(err));

// Your first API endpoint
app.get('/api/hello', function(req, res) {
  res.json({ greeting: 'hello API' });
});


autoIncrement.initialize(mongoose.connection);
const isValidUrl = (urlString) => {
  try {
    const url = new URL(urlString);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch (err) {
    console.log(err)
    return false;
  }
};

app.post('/api/shorturl', async (req, res) => {
  const { originalUrl } = req.body;

  if (!originalUrl || !isValidUrl(originalUrl)) {
    return res.status(400).json({ error: 'Invalid URL' });
  }

  // Verify the URL
  const hostname = new URL(originalUrl).hostname;
  dns.lookup(hostname, async (err) => {
    if (err) {
      console.log(err)
      return res.status(400).json({ error: 'Invalid URL' });
    }

    try {
      let url = await Url.findOne({ originalUrl });
      if (url) {
        res.json({ original_url: url.originalUrl, short_url: url.shortUrl });
      } else {
        url = new Url({ originalUrl });
        await url.save();
        res.json({ original_url: url.originalUrl, short_url: url.shortUrl });
      }
    } catch (err) {
      console.error(err);
      res.status(500).json('Server error');
    }
  });
});



app.get('/api/shorturl/:shortUrl', async function(req, res) {
  try {
    const url = await Url.findOne({ shortUrl: req.params.shortUrl });
    if (url) {
      return res.redirect(url.originalUrl);
    } else {
      return res.status(404).json('No URL found');
    }
  } catch (err) {
    console.error(err);
    res.status(500).json('Server error');
  }
})


app.listen(port, function() {
  console.log(`Listening on port ${port}`);
});
