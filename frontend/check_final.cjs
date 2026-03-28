const fs = require('fs');
const path = require('path');

function getFiles(dir) {
    let results = [];
    const list = fs.readdirSync(dir);
    list.forEach(file => {
        file = dir + '/' + file;
        const stat = fs.statSync(file);
        if (stat && stat.isDirectory()) {
            results = results.concat(getFiles(file));
        } else {
            if (file.endsWith('.vue') || file.endsWith('.ts') || file.endsWith('.js')) {
                results.push(file);
            }
        }
    });
    return results;
}

const allFiles = getFiles('d:/Tiga/frontend/src');
const componentsDir = 'd:/Tiga/frontend/src/features/workflow/components';
const components = getFiles(componentsDir).filter(f => f.endsWith('.vue'));

components.forEach(comp => {
    const basename = path.basename(comp, '.vue');
    let count = 0;
    allFiles.forEach(f => {
        // Only check files other than the component itself
        if (path.normalize(f) !== path.normalize(comp)) {
            const content = fs.readFileSync(f, 'utf8');
            if (content.includes(basename)) count++;
        }
    });
    if (count === 0) {
        console.log(`Unused: ${comp}`);
    }
});
