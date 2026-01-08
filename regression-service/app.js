const express = require("express");
const axios = require("axios");
const Redis = require("ioredis");

const app = express();
app.use(express.json());
