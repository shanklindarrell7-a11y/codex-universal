/**
 * Tests for LeadingTheWay
 */

const { main } = require('../src/index');
const assert = require('assert');

console.log('Running tests...');

try {
  // Test: main function should execute without errors
  main();
  console.log('✓ main function executes without errors');
} catch (error) {
  console.error('✗ main function threw an error:', error);
  process.exit(1);
}

console.log('\nAll tests passed!');
