// Extend from root PostCSS config
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const config = require("../../postcss.config.js");

export default config;
