const fs = require('fs');
const files = [
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\TemplateCard.vue',
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\NodeList.vue',
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\NodeDetail.vue',
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\GatewayInfo.vue',
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\StatCard.vue',
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\LogPanel.vue',
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\TaskTree.vue'
];
const regex = /TemplateCard|NodeList|NodeDetail|GatewayInfo|StatCard|LogPanel|TaskTree/g;

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
allFiles.forEach(f => {
    const content = fs.readFileSync(f, 'utf8');
    const matches = content.match(regex);
    if(matches && !files.includes(f.replace(/\//g, '\\'))) {
        console.log(`File: ${f}`);
        console.log(`Matches: ${[...new Set(matches)].join(', ')}`);
    }
});
