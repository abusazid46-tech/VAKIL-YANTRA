const fs = require('fs');
const path = require('path');
const { processPdfFile, slugify } = require('./statutory_processor');

const SOURCE_DIR = 'C:/Users/sonow/OneDrive/Desktop/Legal Data/Central Act';
const OUTPUT_DIR = path.resolve(__dirname, '../db/extracted_acts');
const REGISTRY_PATH = path.join(OUTPUT_DIR, 'master_validation_registry.json');
const CONSOLIDATED_PATH = path.join(OUTPUT_DIR, 'consolidated_rag_sections.json');

// Core litigation priority files to process first
const CORE_PRIORITY_FILES = [
  'The Bharatiya Nagarik Suraksha Sanhita, 2023.pdf',
  'The Bharatiya Nyaya Sanhita, 2023.pdf',
  'The Bharatiya Sakshya Adhiniyam, 2023.pdf',
  'THE NEGOTIABLE INSTRUMENTS ACT, 1881.pdf',
  'The Limitation Act, 1963.pdf',
  'The Indian Contract Act, 1872.pdf',
  'The Arbitration and Conciliation Act, 1996.pdf',
  'The Commercial Courts Act, 2015.pdf',
  'The Advocates Act, 1961.pdf',
  'The Information Technology Act, 2000.pdf',
  'The Consumer Protection Act, 2019.pdf',
  'The Contempt of Courts Act, 1971.pdf',
  'The Court-Fees Act, 1870.pdf',
  'The Bankers Books Evidence Act, 1891.pdf',
  'The Prohibition of Benami Property Transactions Act, 1988.pdf',
  'The India International Arbitration Centre Act, 2019.pdf',
  'The Code of Civil Procedure, 1908.pdf',
  'The Insolvency and Bankruptcy Code, 2016.pdf',
  'The Companies Act, 2013.pdf'
];

async function run() {
  if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  let registry = {
    started_at: new Date().toISOString(),
    last_updated: new Date().toISOString(),
    total_files_in_source: 649,
    total_processed: 0,
    validation_passed_count: 0,
    validation_notices_count: 0,
    flagged_for_review_count: 0,
    failed_error_count: 0,
    total_chunks_indexed: 0,
    acts: {}
  };

  if (fs.existsSync(REGISTRY_PATH)) {
    try {
      registry = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf-8'));
    } catch {}
  }

  console.log(`\n======================================================`);
  console.log(`INGESTION RUN: ${CORE_PRIORITY_FILES.length} Priority Practice Acts`);
  console.log(`======================================================\n`);

  for (let i = 0; i < CORE_PRIORITY_FILES.length; i++) {
    const filename = CORE_PRIORITY_FILES[i];
    const pdfPath = path.join(SOURCE_DIR, filename);
    const actSlug = slugify(filename.replace(/\.pdf$/i, ''));
    const validationPath = path.join(OUTPUT_DIR, `${actSlug}_validation.json`);

    if (!fs.existsSync(pdfPath)) {
      console.warn(`[${i + 1}/${CORE_PRIORITY_FILES.length}] NOT FOUND: ${filename}`);
      continue;
    }

    if (fs.existsSync(validationPath)) {
      try {
        const valData = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
        if (valData.status.startsWith('VALIDATION_PASSED')) {
          console.log(`[${i + 1}/${CORE_PRIORITY_FILES.length}] ALREADY COMPLETE: ${filename} (${valData.status})`);
          registry.acts[actSlug] = {
            filename,
            act_name: valData.act_name,
            act_number: valData.act_number,
            status: valData.status,
            chunks: valData.total_chunks_produced || valData.total_body_sections_extracted,
            missing: valData.missing_sections.length,
            duplicates: valData.duplicate_sections.length,
            processed_at: registry.acts[actSlug]?.processed_at || new Date().toISOString()
          };
          continue;
        }
      } catch {}
    }

    console.log(`\n[${i + 1}/${CORE_PRIORITY_FILES.length}] PROCESSING: ${filename}`);
    const startMs = Date.now();
    try {
      const result = await processPdfFile(pdfPath, OUTPUT_DIR);
      const val = result.validation;
      const durationSec = ((Date.now() - startMs) / 1000).toFixed(1);

      registry.acts[actSlug] = {
        filename,
        act_name: val.act_name,
        act_number: val.act_number,
        act_year: val.act_year,
        enactment_date: val.enactment_date,
        status: val.status,
        chunks: val.total_chunks_produced,
        body_sections: val.total_body_sections_extracted,
        schedule_items: val.total_schedule_items_extracted,
        missing_sections: val.missing_sections,
        duplicate_sections: val.duplicate_sections,
        repealed_sections_count: val.repealed_sections.length,
        amending_acts_count: val.amending_acts_identified.length,
        duration_seconds: parseFloat(durationSec),
        processed_at: new Date().toISOString()
      };
      console.log(`COMPLETED: ${val.status} | Chunks: ${val.total_chunks_produced} | ${durationSec}s`);
    } catch (err) {
      console.error(`ERROR on ${filename}:`, err.message);
      registry.acts[actSlug] = {
        filename,
        status: 'FAILED_ERROR',
        error: err.message,
        processed_at: new Date().toISOString()
      };
    }

    // Update Registry Metrics
    const actsArray = Object.values(registry.acts);
    registry.total_processed = actsArray.length;
    registry.validation_passed_count = actsArray.filter(a => a.status === 'VALIDATION_PASSED').length;
    registry.validation_notices_count = actsArray.filter(a => a.status === 'VALIDATION_PASSED_WITH_NOTICES').length;
    registry.flagged_for_review_count = actsArray.filter(a => a.status === 'FLAGGED_FOR_REVIEW').length;
    registry.failed_error_count = actsArray.filter(a => a.status === 'FAILED_ERROR').length;
    registry.total_chunks_indexed = actsArray.reduce((acc, a) => acc + (a.chunks || 0), 0);
    registry.last_updated = new Date().toISOString();

    fs.writeFileSync(REGISTRY_PATH, JSON.stringify(registry, null, 2), 'utf-8');
  }

  // Consolidate RAG index
  console.log(`\nRe-consolidating RAG index...`);
  const consolidated = [];
  const files = fs.readdirSync(OUTPUT_DIR).filter(f => f.endsWith('.json') && !f.endsWith('_validation.json') && f !== 'master_validation_registry.json' && f !== 'consolidated_rag_sections.json');

  for (const j of files) {
    try {
      const actData = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, j), 'utf-8'));
      if (Array.isArray(actData.chunks)) {
        for (const c of actData.chunks) {
          consolidated.push({
            id: c.chunk_id,
            act_id: c.act_id,
            act_title: c.act_name,
            chapter: c.chapter,
            section_number: c.section,
            section_title: c.section_title,
            content: c.text,
            chunk_type: c.chunk_type || 'section',
            source_url: `https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=${encodeURIComponent(c.act_name)}`,
            source_page: c.source_page,
            amendment_information: c.amendment_information,
            effective_date: c.effective_date
          });
        }
      }
    } catch {}
  }
  fs.writeFileSync(CONSOLIDATED_PATH, JSON.stringify(consolidated, null, 2), 'utf-8');

  console.log(`\n================ RUN COMPLETED ================`);
  console.log(`Total Validated Acts in Corpus: ${registry.total_processed}`);
  console.log(`Total Clean Passed (100% Sequence): ${registry.validation_passed_count}`);
  console.log(`Total Passed With Notices: ${registry.validation_notices_count}`);
  console.log(`Total Legal RAG Chunks Indexed: ${consolidated.length}`);
  console.log(`Master Registry: ${REGISTRY_PATH}`);
  console.log(`Consolidated RAG File: ${CONSOLIDATED_PATH}`);
  console.log(`===============================================\n`);
}

run().catch(console.error);
