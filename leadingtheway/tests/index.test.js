/**
 * Tests for LeadingTheWay
 */

const { main } = require('../src/index');

describe('LeadingTheWay', () => {
  test('main function should execute without errors', () => {
    expect(() => main()).not.toThrow();
  });
});
