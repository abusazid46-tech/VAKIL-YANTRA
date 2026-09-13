const fs = require('fs');
const path = require('path');
const { processPdfFile, slugify } = require('./statutory_processor');

/**
 * Batch Statutory Ingestion Manager
 * Strictly enforces:
 * - One PDF at a time processing
 * - 14-point validation audit for every single Act
 * - Checkpointing & Master Validation Registry
 * - Skips already-validated files for fault tolerance
 */

const SOURCE_DIR = 'C:/Users/sonow/OneDrive/Desktop/Legal Data/Central Act';
const OUTPUT_DIR = path.resolve(__dirname, '../db/extracted_acts');
const REGISTRY_PATH = path.join(OUTPUT_DIR, 'master_validation_registry.json');
const CONSOLIDATED_PATH = path.join(OUTPUT_DIR, 'consolidated_rag_sections.json');

async function runBatch() {
  const args = process.argv.slice(2);
  let limit = 0; // 0 = all
  let filterKeyword = '';
  let force = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--limit' && args[i + 1]) {
      limit = parseInt(args[i + 1], 10);
      i++;
    } else if (args[i] === '--filter' && args[i + 1]) {
      filterKeyword = args[i + 1].toLowerCase();
      i++;
    } else if (args[i] === '--force') {
      force = true;
    }
  }

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Load or initialize Master Validation Registry
  let registry = {
    started_at: new Date().toISOString(),
    last_updated: new Date().toISOString(),
    total_files_in_source: 0,
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
    } catch (e) {
      console.warn('Could not parse existing registry, starting fresh.');
    }
  }

  // Read all PDF files
  const allFiles = fs.readdirSync(SOURCE_DIR).filter(f => f.toLowerCase().endsWith('.pdf'));
  registry.total_files_in_source = allFiles.length;

  let targetFiles = allFiles;
  if (filterKeyword) {
    targetFiles = allFiles.filter(f => f.toLowerCase().includes(filterKeyword));
    console.log(`Filter "${filterKeyword}" matched ${targetFiles.length} files.`);
  }

  if (limit > 0) {
    targetFiles = targetFiles.slice(0, limit);
    console.log(`Processing limit set to: ${limit} files.`);
  }

  console.log(`\n======================================================`);
  console.log(`BATCH STATUTORY INGESTION & VALIDATION WORKER`);
  console.log(`Total Source PDFs: ${allFiles.length}`);
  console.log(`Queue for this run: ${targetFiles.length}`);
  console.log(`======================================================\n`);

  let count = 0;
  for (const filename of targetFiles) {
    count++;
    const pdfPath = path.join(SOURCE_DIR, filename);
    const actSlug = slugify(filename.replace(/\.pdf$/i, ''));
    const actJsonPath = path.join(OUTPUT_DIR, `${actSlug}.json`);
    const validationPath = path.join(OUTPUT_DIR, `${actSlug}_validation.json`);

    // Check if already validated
    if (!force && fs.existsSync(actJsonPath) && fs.existsSync(validationPath)) {
      try {
        const valData = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
        if (valData.status.startsWith('VALIDATION_PASSED')) {
          console.log(`[${count}/${targetFiles.length}] SKIP (Already Validated): ${filename}`);
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
      } catch {
        // reprocess if corrupt
      }
    }

    console.log(`\n[${count}/${targetFiles.length}] PROCESSING: ${filename}`);
    const startMs = Date.now();

    try {
      const result = await processPdfFile(pdfPath, OUTPUT_DIR);
      const durationSec = ((Date.now() - startMs) / 1000).toFixed(1);
      const val = result.validation;

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

      console.log(`RESULT: ${val.status} | Chunks: ${val.total_chunks_produced} | Duration: ${durationSec}s`);
    } catch (err) {
      console.error(`FAILED on ${filename}:`, err.message);
      registry.acts[actSlug] = {
        filename,
        status: 'FAILED_ERROR',
        error: err.message,
        processed_at: new Date().toISOString()
      };
    }

    // Recalculate summary metrics
    const actsArray = Object.values(registry.acts);
    registry.total_processed = actsArray.length;
    registry.validation_passed_count = actsArray.filter(a => a.status === 'VALIDATION_PASSED').length;
    registry.validation_notices_count = actsArray.filter(a => a.status === 'VALIDATION_PASSED_WITH_NOTICES').length;
    registry.flagged_for_review_count = actsArray.filter(a => a.status === 'FLAGGED_FOR_REVIEW').length;
    registry.failed_error_count = actsArray.filter(a => a.status === 'FAILED_ERROR').length;
    registry.total_chunks_indexed = actsArray.reduce((acc, a) => acc + (a.chunks || 0), 0);
    registry.last_updated = new Date().toISOString();

    // Checkpoint registry after every single Act
    fs.writeFileSync(REGISTRY_PATH, JSON.stringify(registry, null, 2), 'utf-8');
  }

  // Update Consolidated Sections Index for RAG
  console.log(`\nConsolidating validated provisions for Legal RAG Index...`);
  const consolidated = [];
  const filesInOutputDir = fs.readdirSync(OUTPUT_DIR).filter(f => f.endsWith('.json') && !f.endsWith('_validation.json') && f !== 'master_validation_registry.json' && f !== 'consolidated_rag_sections.json');

  for (const jsonFile of filesInOutputDir) {
    try {
      const actData = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, jsonFile), 'utf-8'));
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
    } catch {
      // ignore
    }
  }

  fs.writeFileSync(CONSOLIDATED_PATH, JSON.stringify(consolidated, null, 2), 'utf-8');
  console.log(`Consolidated RAG Index: ${CONSOLIDATED_PATH} (${consolidated.length} total legal provisions)`);

  console.log(`\n================ BATCH SUMMARY ================`);
  console.log(`Total Source PDFs: ${registry.total_files_in_source}`);
  console.log(`Total Processed So Far: ${registry.total_processed}`);
  console.log(`Validation Passed (100% clean): ${registry.validation_passed_count}`);
  console.log(`Validation Passed (With Notices): ${registry.validation_notices_count}`);
  console.log(`Flagged For Review: ${registry.flagged_for_review_count}`);
  console.log(`Failed Errors: ${registry.failed_error_count}`);
  console.log(`Total Chunks in RAG Index: ${registry.total_chunks_indexed}`);
  console.log(`Master Registry: ${REGISTRY_PATH}`);
  console.log(`================================================\n`);
}

runBatch().catch(err => {
  console.error('Batch run terminated:', err);
  process.exit(1);
});
