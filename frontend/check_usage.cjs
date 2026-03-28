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

const workflowFileNames = workflowFiles.map(f => path.basename(f).replace(/\.(vue|ts|js)$/, ''));

const usages = {};
workflowFileNames.forEach(name => usages[name] = 0);

allSrcFiles.forEach(file => {
    const content = fs.readFileSync(file, 'utf-8');
    workflowFileNames.forEach(name => {
        // Simple heuristic: check if the component/file name is mentioned
        const regex = new RegExp(`\\b${name}\\b`, 'g');
        const matches = content.match(regex);
        if (matches) {
            usages[name] += matches.length;
        }
    });
});

console.log("Usage counts:");
Object.keys(usages).forEach(name => {
    if (usages[name] <= 1) { // 1 might be the file's own export/definition
        console.log(`Low usage (<=1): ${name} (${usages[name]} matches)`);
    } else {
        console.log(`Used: ${name} (${usages[name]} matches)`);
    }
});
