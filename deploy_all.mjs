import fs from 'fs';
import path from 'path';

const TOKEN = process.argv[2] || process.env.VERCEL_TOKEN;
const IS_DRY_RUN = process.argv.includes('--dry-run');

if (!TOKEN && !IS_DRY_RUN) {
  console.error('Usage: node deploy_all.mjs <VERCEL_TOKEN>');
  console.error('       node deploy_all.mjs --dry-run');
  process.exit(1);
}

const BACKEND_PROJ = 'prj_dqLWFWD3nrdKEW9QUbTKkyj3ubeV'; // vakil-yantra-api
const FRONTEND_PROJ = 'prj_LAtF0cWospCY10DIPddAKrXuOsLX'; // web

const ROOT_DIR = process.cwd();
const BACKEND_DIR = path.join(ROOT_DIR, 'backend');
const WEB_DIR = path.join(ROOT_DIR, 'web');

function getFilesRecursively(dir, baseDir = dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  let files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    const relPath = path.relative(baseDir, fullPath).replace(/\\/g, '/');

    if (
      entry.name === '.git' ||
      entry.name === '__pycache__' ||
      entry.name === '.venv' ||
      entry.name === 'node_modules' ||
      entry.name === '.next' ||
      entry.name.endsWith('.pyc') ||
      entry.name.endsWith('.db') ||
      (relPath.includes('extracted_acts') && entry.name !== 'consolidated_rag_sections.json' && !entry.isDirectory())
    ) {
      continue;
    }

    if (entry.isDirectory()) {
      files = files.concat(getFilesRecursively(fullPath, baseDir));
    } else {
      files.push({
        file: relPath,
        data: fs.readFileSync(fullPath).toString('base64'),
        encoding: 'base64'
      });
    }
  }
  return files;
}

async function deployProject(name, projectId, dir) {
  console.log(`\n========================================`);
  console.log(`Deploying ${name} to Vercel (Project: ${projectId})...`);
  console.log(`Source directory: ${dir}`);

  const files = getFilesRecursively(dir);
  console.log(`Prepared ${files.length} files for deployment.`);

  if (IS_DRY_RUN) {
    console.log(`[DRY RUN] First 5 files:`, files.slice(0, 5).map(f => f.file));
    console.log(`[DRY RUN] Would deploy ${files.length} files to ${projectId}.`);
    return { dryRun: true };
  }

  const res = await fetch(`https://api.vercel.com/v13/deployments`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: name,
      project: projectId,
      target: 'production',
      files: files
    })
  });

  const body = await res.json();
  if (!res.ok) {
    console.error(`Deployment failed with status ${res.status}:`, body);
    throw new Error(`Deployment of ${name} failed`);
  }

  console.log(`Deployment created: ${body.id}`);
  console.log(`Building at: https://${body.url}`);

  // Poll for readiness
  let readyState = body.readyState;
  for (let attempt = 1; attempt <= 45; attempt++) {
    await new Promise(r => setTimeout(r, 4000));
    const checkRes = await fetch(`https://api.vercel.com/v13/deployments/${body.id}`, {
      headers: { Authorization: `Bearer ${TOKEN}` }
    });
    const checkData = await checkRes.json();
    readyState = checkData.readyState;
    console.log(`[Attempt ${attempt}] Status: ${readyState}`);
    if (readyState === 'READY') {
      console.log(`>>> ${name} is LIVE and READY!`);
      console.log(`URLs:`, checkData.alias || body.url);
      return checkData;
    } else if (readyState === 'ERROR' || readyState === 'CANCELED') {
      throw new Error(`${name} deployment ended with state: ${readyState}`);
    }
  }
  throw new Error(`${name} deployment timed out`);
}

async function main() {
  console.log('Starting automated production deployment for Vakil Yantra...');
  
  // 1. Deploy Backend API
  await deployProject('vakil-yantra-api', BACKEND_PROJ, BACKEND_DIR);

  // 2. Deploy Web Frontend
  await deployProject('web', FRONTEND_PROJ, WEB_DIR);

  console.log('\n========================================');
  console.log('SUCCESS! Both Backend API and Web Frontend are deployed and live in production!');
}

main().catch(err => {
  console.error('\nFatal deployment error:', err.message || err);
  process.exit(1);
});
