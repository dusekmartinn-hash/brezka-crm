// REALITNI SCRAPER - Praha-zapad, Beroun, Pribram, Benesov + Harrachov
// Zdroj: sreality.cz
// Prvni spusteni: spust nastavTrigger(), pak resetANaplnZnovu_()

// ===================================================
// KONFIGURACE
// ===================================================

var CFG = {
  maxCenaDum:     6000000,
  maxCenaPozemek: 3000000,
  renovaceBudget: 3000000,
  // sreality.cz district IDs pro hlavni oblasti
  distIds: [5048, 5003, 5049, 5002], // Praha-zapad, Beroun, Pribram, Benesov
  // sreality.cz region ID pro Liberecky kraj (Harrachov)
  libereckyKrajId: 7,
};

var TAB = {
  domy:      'Domy & Chaty',
  pozemky:   'Pozemky',
  harrachov: 'Harrachov',
  archiv:    'Archiv',
  log:       'Log',
};

var HLAVICKA_DOMY = [
  'ID', 'Pridano', 'Zdroj', 'Nazev inzeratu', 'Obec', 'Okres',
  'Cena (Kc)', 'Plocha (m2)', 'Stav objektu', 'Rozpocet', 'Status', 'Odkaz'
];

var HLAVICKA_POZEMKY = [
  'ID', 'Pridano', 'Zdroj', 'Nazev inzeratu', 'Obec', 'Okres',
  'Cena (Kc)', 'Plocha (m2)', 'Typ pozemku', 'Status', 'Odkaz'
];

var HLAVICKA_HARRACHOV = [
  'ID', 'Pridano', 'Zdroj', 'Nazev inzeratu', 'Typ',
  'Cena (Kc)', 'Plocha (m2)', 'Stav objektu', 'Rozpocet', 'Status', 'Odkaz'
];

// ===================================================
// STAV & ROZPOCET INDIKATOR
// ===================================================

var STAV_KW = {
  novy: [
    'novostavba', 'nova stavba', 'po rekonstrukci', 'kompletni rekonstrukce',
    'novy stav', 'zrekonstruovany', 'zrekonstruovana', 'vyborny stav'
  ],
  oprava: [
    'k rekonstrukci', 'puvodni stav', 'nutna rekonstrukce', 'pred rekonstrukci',
    'zchatrary', 'starsi stavba', 'vyzaduje rekonstrukci'
  ],
  castecny: [
    'castecna rekonstrukce', 'castecne zrekonstruo', 'dobry stav',
    'zachovaly stav', 'udrzovany'
  ]
};

function detekujStav_(text) {
  var t = (text || '').toLowerCase();
  var i;
  for (i = 0; i < STAV_KW.novy.length; i++) {
    if (t.indexOf(STAV_KW.novy[i]) >= 0) return 'Novy/po rekonstrukci';
  }
  for (i = 0; i < STAV_KW.oprava.length; i++) {
    if (t.indexOf(STAV_KW.oprava[i]) >= 0) return 'K rekonstrukci';
  }
  for (i = 0; i < STAV_KW.castecny.length; i++) {
    if (t.indexOf(STAV_KW.castecny[i]) >= 0) return 'Castecne';
  }
  return 'Neurceno';
}

function rozpocetFit_(cena, stav) {
  if (stav === 'Novy/po rekonstrukci') {
    return cena <= CFG.maxCenaDum ? 'Sedi' : 'Nad rozpocet';
  }
  if (stav === 'K rekonstrukci') {
    if (cena <= 3000000) return 'Sedi + rekonstrukce';
    if (cena <= 4500000) return 'Hranicne';
    return 'Nad rozpocet';
  }
  if (stav === 'Castecne') {
    return cena <= 4500000 ? 'Posoudit' : 'Nad rozpocet';
  }
  return 'Posoudit';
}

// ===================================================
// SREALITY - URL z SEO dat
// ===================================================

var SUBCAT_SLUG = {
  37: 'rodinny-dum',
  38: 'vila',
  39: 'chalupa',
  40: 'chata',
  41: 'zemedelska-usedlost',
  42: 'bytovy-dum',
  47: 'ostatni',
  56: 'stavebni-pozemek',
  57: 'pole',
  58: 'les',
  59: 'zahrada',
  60: 'ostatni-pozemek'
};

var MAINCAT_SLUG = {
  2: 'domy',
  3: 'pozemky'
};

function sestavUrl_(e, hashId) {
  var seo      = e.seo || {};
  var mainCat  = MAINCAT_SLUG[e.category_main_cb || 2] || 'domy';
  var subCat   = SUBCAT_SLUG[e.category_sub_cb || 0] || '-';
  var locality = seo.locality || '-';
  return 'https://www.sreality.cz/detail/prodej/' + mainCat + '/' + subCat + '/' + locality + '/' + hashId;
}

function detekujTypDomu_(text) {
  var t = (text || '').toLowerCase();
  if (t.indexOf('chata') >= 0)    return 'Chata';
  if (t.indexOf('chalupa') >= 0)  return 'Chalupa';
  if (t.indexOf('apartman') >= 0) return 'Apartman';
  if (t.indexOf('penzion') >= 0)  return 'Penzion';
  if (t.indexOf('vila') >= 0)     return 'Vila';
  return 'Rodinny dum';
}

function detekujTypPozemku_(text) {
  var t = (text || '').toLowerCase();
  if (t.indexOf('stavebni') >= 0)                              return 'Stavebni';
  if (t.indexOf('zemedelsky') >= 0 || t.indexOf('orna') >= 0) return 'Zemedeslky';
  if (t.indexOf('les') >= 0)                                   return 'Lesni';
  if (t.indexOf('zahrada') >= 0)                               return 'Zahrada';
  return 'Ostatni';
}

// ===================================================
// SREALITY - fetch + parse
// ===================================================

function fetchSreality_(categoryMain, params, priceMax) {
  var url = 'https://www.sreality.cz/api/cs/v2/estates'
    + '?category_main_cb=' + categoryMain
    + '&category_type_cb=1'
    + '&' + params
    + (priceMax ? '&price_to=' + priceMax : '')
    + '&per_page=100&page=1';
  try {
    var resp = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      headers: { 'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json' }
    });
    if (resp.getResponseCode() !== 200) {
      loguj_('Sreality HTTP ' + resp.getResponseCode() + ' | ' + url.substring(0, 80));
      return [];
    }
    var data = JSON.parse(resp.getContentText());
    return (data && data._embedded && data._embedded.estates) ? data._embedded.estates : [];
  } catch (ex) {
    loguj_('Sreality chyba: ' + ex.toString());
    return [];
  }
}

function parseEstateDomy_(e) {
  var hashId   = String(e.hash_id || e.id || '');
  var locality = e.locality || '';
  var parts    = locality.split(',');
  return {
    id:     'SR_' + hashId,
    zdroj:  'sreality.cz',
    nazev:  e.name || '',
    obec:   parts[0] ? parts[0].trim() : '',
    okres:  parts[1] ? parts[1].trim() : '',
    cena:   e.price || 0,
    plocha: e.area || e.usable_area || 0,
    odkaz:  sestavUrl_(e, hashId)
  };
}

function parseEstatePozemky_(e) {
  var hashId   = String(e.hash_id || e.id || '');
  var locality = e.locality || '';
  var parts    = locality.split(',');
  return {
    id:     'SR_' + hashId,
    zdroj:  'sreality.cz',
    nazev:  e.name || '',
    obec:   parts[0] ? parts[0].trim() : '',
    okres:  parts[1] ? parts[1].trim() : '',
    cena:   e.price || 0,
    plocha: e.area || e.usable_area || 0,
    typ:    detekujTypPozemku_(e.name || ''),
    odkaz:  sestavUrl_(e, hashId)
  };
}

function parseEstateHarrachov_(e) {
  var hashId = String(e.hash_id || e.id || '');
  var stav   = detekujStav_(e.name || '');
  return {
    id:     'SR_HARR_' + hashId,
    zdroj:  'sreality.cz',
    nazev:  e.name || '',
    typ:    e.category_main_cb === 3 ? detekujTypPozemku_(e.name || '') : detekujTypDomu_(e.name || ''),
    cena:   e.price || 0,
    plocha: e.area || e.usable_area || 0,
    stav:   stav,
    fit:    rozpocetFit_(e.price || 0, stav),
    odkaz:  sestavUrl_(e, hashId)
  };
}

// ===================================================
// HARRACHOV
// ===================================================

function fetchHarrachov_() {
  var results = [];
  var categories = [2, 3];

  for (var c = 0; c < categories.length; c++) {
    var cat    = categories[c];
    // Liberecky kraj = region ID 7
    var estates = fetchSreality_(cat, 'locality_region_id=' + CFG.libereckyKrajId, null);
    loguj_('Harrachov region 7 cat ' + cat + ': nalezeno ' + estates.length + ' v kraji');

    // Loguj prvnich 5 lokalit pro overeni ze jsme ve spravnem regionu
    if (estates.length > 0 && results.length === 0) {
      var sample = [];
      for (var s = 0; s < Math.min(5, estates.length); s++) {
        sample.push(estates[s].locality || '?');
      }
      loguj_('Ukazka lokalit: ' + sample.join(' | '));
    }

    for (var i = 0; i < estates.length; i++) {
      var e        = estates[i];
      var locality = (e.locality || '').toLowerCase();
      if (locality.indexOf('harrachov') < 0) continue;
      results.push(parseEstateHarrachov_(e));
    }
    Utilities.sleep(400);
  }

  loguj_('Harrachov: celkem ' + results.length + ' inzeratu');
  return results;
}

// ===================================================
// INICIALIZACE ZALOZEK
// ===================================================

function inicializujZalozky_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var definice = [
    { key: 'domy',      hlavicka: HLAVICKA_DOMY },
    { key: 'pozemky',   hlavicka: HLAVICKA_POZEMKY },
    { key: 'harrachov', hlavicka: HLAVICKA_HARRACHOV },
    { key: 'archiv',    hlavicka: HLAVICKA_DOMY },
    { key: 'log',       hlavicka: ['Cas', 'Zprava'] }
  ];
  for (var i = 0; i < definice.length; i++) {
    var def   = definice[i];
    var sheet = ss.getSheetByName(TAB[def.key]);
    if (!sheet) sheet = ss.insertSheet(TAB[def.key]);
    if (sheet.getLastRow() === 0) {
      var h = def.hlavicka;
      sheet.getRange(1, 1, 1, h.length).setValues([h]);
      sheet.getRange(1, 1, 1, h.length)
        .setBackground('#1a1a2e').setFontColor('#ffffff').setFontWeight('bold');
      sheet.setFrozenRows(1);
      if (def.key !== 'log') sheet.setColumnWidth(4, 280);
    }
  }
}

function vymaz_(tabKey) {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB[tabKey]);
  if (!sheet) return;
  var lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    sheet.deleteRows(2, lastRow - 1);
  }
}

// ===================================================
// ZAPIS DO SHEETU
// ===================================================

function nactiExistujiciIDs_(sheet) {
  var ids     = {};
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return ids;
  var data = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (var i = 0; i < data.length; i++) ids[String(data[i][0])] = true;
  return ids;
}

function zapisDomy_(inzeraty) {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB.domy);
  var exist = nactiExistujiciIDs_(sheet);
  var dnes  = Utilities.formatDate(new Date(), 'Europe/Prague', 'dd.MM.yyyy');
  var nove  = [];
  for (var i = 0; i < inzeraty.length; i++) {
    var inz = inzeraty[i];
    if (exist[inz.id]) continue;
    var stav = detekujStav_(inz.nazev);
    nove.push([
      inz.id, dnes, inz.zdroj, inz.nazev,
      inz.obec, inz.okres,
      inz.cena, inz.plocha,
      stav, rozpocetFit_(inz.cena, stav), 'Nove', inz.odkaz
    ]);
  }
  if (nove.length > 0) {
    var row = sheet.getLastRow() + 1;
    sheet.getRange(row, 1, nove.length, HLAVICKA_DOMY.length).setValues(nove);
    sheet.getRange(row, 1, nove.length, HLAVICKA_DOMY.length).setBackground('#e8f5e9');
  }
  loguj_('Domy: pridano ' + nove.length + ' novych z ' + inzeraty.length + ' celkem');
}

function zapisPozemky_(inzeraty) {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB.pozemky);
  var exist = nactiExistujiciIDs_(sheet);
  var dnes  = Utilities.formatDate(new Date(), 'Europe/Prague', 'dd.MM.yyyy');
  var nove  = [];
  for (var i = 0; i < inzeraty.length; i++) {
    var inz = inzeraty[i];
    if (exist[inz.id]) continue;
    nove.push([
      inz.id, dnes, inz.zdroj, inz.nazev,
      inz.obec, inz.okres,
      inz.cena, inz.plocha,
      inz.typ || 'Ostatni', 'Nove', inz.odkaz
    ]);
  }
  if (nove.length > 0) {
    var row = sheet.getLastRow() + 1;
    sheet.getRange(row, 1, nove.length, HLAVICKA_POZEMKY.length).setValues(nove);
    sheet.getRange(row, 1, nove.length, HLAVICKA_POZEMKY.length).setBackground('#e8f5e9');
  }
  loguj_('Pozemky: pridano ' + nove.length + ' novych z ' + inzeraty.length + ' celkem');
}

function zapisHarrachov_(inzeraty) {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB.harrachov);
  var exist = nactiExistujiciIDs_(sheet);
  var dnes  = Utilities.formatDate(new Date(), 'Europe/Prague', 'dd.MM.yyyy');
  var nove  = [];
  for (var i = 0; i < inzeraty.length; i++) {
    var inz = inzeraty[i];
    if (exist[inz.id]) continue;
    nove.push([
      inz.id, dnes, inz.zdroj, inz.nazev,
      inz.typ, inz.cena, inz.plocha,
      inz.stav, inz.fit, 'Nove', inz.odkaz
    ]);
  }
  if (nove.length > 0) {
    var row = sheet.getLastRow() + 1;
    sheet.getRange(row, 1, nove.length, HLAVICKA_HARRACHOV.length).setValues(nove);
    sheet.getRange(row, 1, nove.length, HLAVICKA_HARRACHOV.length).setBackground('#e3f2fd');
  }
  loguj_('Harrachov: pridano ' + nove.length + ' novych');
}

function loguj_(zprava) {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB.log);
  if (!sheet) sheet = ss.insertSheet(TAB.log);
  var cas = Utilities.formatDate(new Date(), 'Europe/Prague', 'dd.MM.yyyy HH:mm:ss');
  sheet.appendRow([cas, zprava]);
}

// ===================================================
// HLAVNI FUNKCE
// ===================================================

function aktualizujInzeraty() {
  inicializujZalozky_();
  loguj_('--- Spusteni aktualizace ---');

  var domyRaw    = fetchSreality_(2, 'locality_district_id=' + CFG.distIds.join(','), CFG.maxCenaDum);
  var pozemkyRaw = fetchSreality_(3, 'locality_district_id=' + CFG.distIds.join(','), CFG.maxCenaPozemek);

  var domy    = [];
  var pozemky = [];
  for (var i = 0; i < domyRaw.length; i++)    domy.push(parseEstateDomy_(domyRaw[i]));
  for (var j = 0; j < pozemkyRaw.length; j++) pozemky.push(parseEstatePozemky_(pozemkyRaw[j]));

  zapisDomy_(domy);
  zapisPozemky_(pozemky);
  zapisHarrachov_(fetchHarrachov_());

  loguj_('--- Hotovo ---');
}

// Vymaze stara data a znovu nacte vse (pouzij kdyz chces opravit URL)
function resetANaplnZnovu_() {
  inicializujZalozky_();
  loguj_('--- RESET: mazem stara data ---');
  vymaz_('domy');
  vymaz_('pozemky');
  vymaz_('harrachov');
  loguj_('Stara data smazana, spoustim naplneni...');
  aktualizujInzeraty();
}

// ===================================================
// NASTAVENI TRIGGERU
// ===================================================

function nastavTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) ScriptApp.deleteTrigger(triggers[i]);
  ScriptApp.newTrigger('aktualizujInzeraty').timeBased().everyDays(1).atHour(7).create();
  loguj_('Trigger nastaven: kazdy den v 7:00');
}
