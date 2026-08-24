/**
 * Base strategy interface for Cinema Ticket Monitors
 */
class BaseStrategy {
  constructor(id, name, description) {
    this.id = id;
    this.name = name;
    this.description = description;
  }

  /**
   * Inspect target website and determine ticket availability
   * @param {Object} target Target object configuration
   * @returns {Promise<Object>} Check result object
   */
  async inspect(target) {
    throw new Error(`inspect() method must be implemented by strategy ${this.id}`);
  }

  /**
   * Helper to format standard check result
   */
  formatResult({ status, isAvailable, movieTitle, bookingUrl, details, rawMatch }) {
    return {
      status, // 'AVAILABLE' | 'COMING_SOON' | 'UNAVAILABLE' | 'ERROR'
      isAvailable: Boolean(isAvailable),
      movieTitle: movieTitle || 'Unknown Movie',
      bookingUrl: bookingUrl || null,
      details: details || '',
      rawMatch: rawMatch || null,
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = BaseStrategy;
