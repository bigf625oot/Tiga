const fs = require('fs');
const path = require('path');

const srcDir = path.join('d:', 'Tiga', 'frontend', 'src');
const workflowDir = path.join(srcDir, 'features', 'workflow');

function getFiles(dir, ext) {
    let results = [];
    const list = fs.readdirSync(dir);
    list.forEach(file => {
        file = path.join(dir, file);
        const stat = fs.statSync(file);
        if (stat && stat.isDirectory()) {
            results = results.concat(getFiles(file, ext));
        } else {
            if (ext.some(e => file.endsWith(e))) results.push(file);
        }
    });
    return results;
}

const allSrcFiles = getFiles(srcDir, ['.ts', '.vue', '.js']);
const workflowFiles = getFiles(workflowDir, ['.ts', '.vue', '.js']);

const workflowFileNames = workflowFiles.map(f => ({
    name: path.basename(f),
    basename: path.basename(f).replace(/\.(vue|ts|js)$/, ''),
    relPath: f.replace(/\\/g, '/').split('features/workflow/')[1]
}));

const usages = {};
workflowFileNames.forEach(f => usages[f.name] = 0);

allSrcFiles.forEach(file => {
    const content = fs.readFileSync(file, 'utf-8');
    workflowFileNames.forEach(f => {
        // check by basename or by partial path
        const regex1 = new RegExp(`\\b${f.basename}\\b`, 'g');
        const regex2 = new RegExp(f.name, 'g');
        if (content.match(regex1) || content.match(regex2)) {
            usages[f.name]++;
        }
    });
});

console.log("File usages (by mentions in any file):");
Object.keys(usages).forEach(name => {
    if (usages[name] <= 1) { // 1 means it only mentions itself or just one mention total
        console.log(`Low usage: ${name} (${usages[name]} matches)`);
    }
});
