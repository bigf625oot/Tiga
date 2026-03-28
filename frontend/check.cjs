const fs = require('fs');
const files = [
    'd:\\Tiga\\frontend\\src\\features\\chat\\components\\blocks\\SoloLayoutBlockRenderer.vue',
    'd:\\Tiga\\frontend\\src\\features\\qa\\components\\SmartQA.vue',
    'd:\\Tiga\\frontend\\src\\features\\chat\\types\\index.ts',
    'd:\\Tiga\\frontend\\src\\features\\workflow\\components\\AutoTaskPanel.vue',
    'd:\\Tiga\\frontend\\src\\features\\qa\\components\\ChatCard.vue',
    'd:\\Tiga\\frontend\\src\\App.vue'
];
files.forEach(f => {
    if(fs.existsSync(f)) {
        const content = fs.readFileSync(f, 'utf8');
        const matches = content.match(/TaskManagement|WorkflowManagement|SmartQATaskPanel|SoloTaskCard/g);
        if(matches) {
            console.log(`File: ${f}`);
            console.log(`Matches: ${[...new Set(matches)].join(', ')}`);
        }
    }
});
