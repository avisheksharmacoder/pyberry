// To start the server:
// node index.js
const express = require('express');
const app = express();
const port = 8000;

app.use(express.json());

app.get('/', (req, res) => {
  res.send('Hello from Node Express endpoint!');
});

app.post('/test-benchmark', (req, res) => {
  const data = req.body;
  res.json({
    status: 'success',
    received_id: data.id,
    received_name: data.name,
    received_active_status: data.is_active
  });
});

app.listen(port, () => {
  console.log(`Node Express backend listening on port ${port}`);
});
