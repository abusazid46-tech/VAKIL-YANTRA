import fs from 'fs';
import path from 'path';

const TOKEN = process.argv[2] || process.env.VERCEL_TOKEN;
if (!TOKEN) {
  console.error('Usage: node deploy_web.mjs <VERCEL_TOKEN>');
  process.exit(1);
}

const TEAM_ID = 'team_mvhc0BgBg4hwt0yuHSjHgkmi';
const PROJ_ID = 'prj_LAtF0cWospCY10DIPddAKrXuOsLX'; // web
const SOURCE_DIR = 'C:\\Users\\sonow\\Documents\\Codex\\vakil-yantra\\web';

function getFilesRecursively(dir, baseDir = dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  let files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    const relPath = path.relative(baseDir, fullPath).replace(/\\/g, '/');

    if (
      entry.name === '.git' ||
      entry.name === 'node_modules' ||
      entry.name === '.next' ||
      entry.name.endsWith('.tsbuildinfo')
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

async function main() {
  console.log('Gathering web frontend files from', SOURCE_DIR);
  const files = getFilesRecursively(SOURCE_DIR);
  console.log(`Prepared ${files.length} files for web deployment:`);
  files.forEach(f => console.log(` - ${f.file}`));

  console.log('\nTriggering Vercel deployment for web frontend...');
  const res = await fetch(`https://api.vercel.com/v13/deployments?teamId=${TEAM_ID}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'web',
      project: PROJ_ID,
      target: 'production',
      files: files
    })
  });

  const body = await res.json();
  if (!res.ok) {
    console.error('Deployment failed:', res.status, body);
    process.exit(1);
  }

  console.log('\nDeployment initiated successfully!');
  console.log('Deployment ID:', body.id);
  console.log('Building at:', body.url);

  console.log('\nWaiting for deployment to build...');
  let readyState = body.readyState;
  for (let attempt = 1; attempt <= 45; attempt++) {
    await new Promise(r => setTimeout(r, 4000));
    const checkRes = await fetch(`https://api.vercel.com/v13/deployments/${body.id}?teamId=${TEAM_ID}`, {
      headers: { Authorization: `Bearer ${TOKEN}` }
    });
    const checkData = await checkRes.json();
    readyState = checkData.readyState;
    console.log(`[Attempt ${attempt}] Status: ${readyState}`);
    if (readyState === 'READY') {
      console.log('\n Web Frontend is READY and live!');
      console.log('Aliases:', checkData.alias);
      break;
    } else if (readyState === 'ERROR' || readyState === 'CANCELED') {
      console.error('\n Deployment failed with state:', readyState);
      process.exit(1);
    }
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
