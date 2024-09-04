/* gulpfile.js */

/**
 * Import uswds-compile
 */
const uswds = require("@uswds/compile");

/**
 * USWDS version
 * Set the major version of USWDS you're using
 * (Current options are the numbers 2 or 3)
 */
uswds.settings.version = 3;

/**
 * Path settings
 * Set as many as you need
 */
uswds.paths.src.projectSass = "./project/static/uswds/sass";
uswds.paths.dist.theme = "./project/static/uswds/sass";
uswds.paths.dist.img = "./project/static/uswds/img";
uswds.paths.dist.fonts = "./project/static/uswds/fonts";
uswds.paths.dist.js = "./project/static/uswds/js";
uswds.paths.dist.css = "./project/static/uswds/css";

/**
 * Exports
 * Add as many as you need
 */
exports.init = uswds.init;
exports.compile = uswds.compile;
exports.watch = uswds.watch;
exports.updateUswds = uswds.updateUswds;
exports.default = uswds.watch;
