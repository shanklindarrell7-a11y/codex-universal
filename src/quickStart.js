// QUICK START FUNCTION
// ============================================

function quickStart() {
  const ui = SpreadsheetApp.getUi();
  
  const response = ui.alert(
    'Quick Start Setup',
    'This will set up your lead automation system. It will:\n\n1. Create the leads sheet\n2. Add sample data\n3. Set up daily automation\n\nContinue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response === ui.Button.YES) {
    createSheet();
    
    // Add some sample data
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.sheetName);
    const sampleLeads = generateMockLeads('plumber', 'New York', 10);
    
    sampleLeads.forEach(lead => {
      sheet.appendRow([
        lead.name,
        lead.phone,
        lead.website,
        lead.address,
        'New York',
        'plumber',
        '',
        'New Lead',
        '',
        ''
      ]);
    });
    
    setupDailyTrigger();
    
    ui.alert('✅ System ready! Click "⚡ Lead Automation" in the menu to start.');
  }
}

SETUP INSTRUCTIONS (3 Minutes)

1. Create a new Google Sheet: sheets.new
2. Open Apps Script: Extensions → Apps Script
3. Paste the entire code above
4. Save the project (Ctrl+S or Cmd+S)
5. Reload the sheet - You'll see "⚡ Lead Automation" in the menu
6. Click "Quick Start" to initialize

Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): 2026-01-08 19:17:08
Current User's Login: shanklindarrell7-a11y