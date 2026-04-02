// P10: Markdown to DOCX Local Micro-Renderer using docx.js
// 这个脚本作为本地转换引擎，接收 Markdown 文件路径并输出 DOCX 文件。
// 相比 pandoc，docx.js 能提供更精细的样式控制和护城河级的排版确定性。

const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } = require('docx');

// 简易的 Markdown 解析器，用于剥离核心业务逻辑
function parseMarkdownToDocxChildren(markdownContent) {
    const lines = markdownContent.split('\n');
    const children = [];

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
            // 空行增加段落间距
            children.push(new Paragraph({ text: "", spacing: { after: 120 } }));
            continue;
        }

        // 处理标题
        if (trimmed.startsWith('# ')) {
            children.push(new Paragraph({
                text: trimmed.substring(2),
                heading: HeadingLevel.HEADING_1,
                alignment: AlignmentType.CENTER,
                spacing: { before: 240, after: 120 }
            }));
        } else if (trimmed.startsWith('## ')) {
            children.push(new Paragraph({
                text: trimmed.substring(3),
                heading: HeadingLevel.HEADING_2,
                spacing: { before: 240, after: 120 }
            }));
        } else if (trimmed.startsWith('### ')) {
            children.push(new Paragraph({
                text: trimmed.substring(4),
                heading: HeadingLevel.HEADING_3,
                spacing: { before: 240, after: 120 }
            }));
        } 
        // 处理无序列表
        else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            children.push(new Paragraph({
                text: trimmed.substring(2),
                bullet: { level: 0 }
            }));
        }
        // 处理粗体 (简易处理，仅支持整行粗体或无粗体)
        else if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
            children.push(new Paragraph({
                children: [
                    new TextRun({
                        text: trimmed.substring(2, trimmed.length - 2),
                        bold: true
                    })
                ],
                spacing: { after: 120 }
            }));
        }
        // 普通段落
        else {
            children.push(new Paragraph({
                children: [new TextRun(trimmed)],
                spacing: { after: 120 }
            }));
        }
    }
    return children;
}

async function renderDocx(inputPath, outputPath) {
    try {
        const mdContent = fs.readFileSync(inputPath, 'utf8');
        const children = parseMarkdownToDocxChildren(mdContent);

        const doc = new Document({
            creator: "Tiga Agent System",
            title: "Generated Document",
            description: "Automatically generated from Markdown via local engine",
            styles: {
                default: {
                    document: {
                        run: { font: "Arial", size: 24 } // 12pt
                    }
                }
            },
            sections: [{
                properties: {
                    page: {
                        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } // 1 inch margins
                    }
                },
                children: children
            }]
        });

        const buffer = await Packer.toBuffer(doc);
        fs.writeFileSync(outputPath, buffer);
        console.log(`SUCCESS: ${outputPath}`);
    } catch (error) {
        console.error(`ERROR: ${error.message}`);
        process.exit(1);
    }
}

const args = process.argv.slice(2);
if (args.length < 2) {
    console.error("Usage: node md_to_docx.js <input.md> <output.docx>");
    process.exit(1);
}

renderDocx(args[0], args[1]);