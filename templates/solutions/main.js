"use strict";

const tokens = require("fs").readFileSync(0, "utf8").split(/\s+/).filter(Boolean);
const n = Number(tokens[0]);

console.log(n);
