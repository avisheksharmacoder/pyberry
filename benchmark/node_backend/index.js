const express = require('express');
const app = express();
const port = 8000;

app.get('/', (req, res) => {
  res.send('Hello from Node Express endpoint!');
});

app.listen(port, () => {
  console.log(`Node Express backend listening on port ${port}`);
});
