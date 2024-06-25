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
const Counter = require('./Counter');

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
  const { url } = req.body;

  if (!url || !isValidUrl(url)) {
    return res.json({ error: 'invalid URL' });
  }

  const hostname = new URL(url).hostname;
  dns.lookup(hostname, async (err) => {
    if (err) {
      return res.json({ error: 'invalid URL' });
    }

    try {
      let foundUrl = await Url.findOne({ originalUrl: url });
      if (foundUrl) {
        return res.json({ original_url: foundUrl.originalUrl, short_url: foundUrl.shortUrl });
      } else {
        // Get the current counter value and increment it
        let counter = await Counter.findOneAndUpdate({}, { $inc: { count: 1 } }, { new: true, upsert: true });
        let shortUrl = counter.count;

        foundUrl = new Url({ originalUrl: url, shortUrl });
        await foundUrl.save();
        return res.json({ original_url: foundUrl.originalUrl, short_url: foundUrl.shortUrl });
      }
    } catch (err) {
      console.error(err);
      return res.status(500).json('Server error');
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
    return res.status(500).json('Server error');
  }
})


app.listen(port, function() {
  console.log(`Listening on port ${port}`);
});
