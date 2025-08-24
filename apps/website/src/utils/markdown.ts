import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import matter from 'gray-matter';
import { marked } from 'marked';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const contentDir = path.join(__dirname, '../../../..');

export interface MarkdownFile {
  content: string;
  data: {
    [key: string]: any;
  };
  filePath: string;
}

export async function getMarkdownFiles(directory: string = ''): Promise<MarkdownFile[]> {
  const fullPath = path.join(contentDir, directory);
  const files = fs.readdirSync(fullPath);
  
  const markdownFiles = await Promise.all(
    files.map(async (file) => {
      if (!file.endsWith('.md')) return null;
      
      const filePath = path.join(directory, file);
      const fullFilePath = path.join(contentDir, filePath);
      const fileContents = fs.readFileSync(fullFilePath, 'utf8');
      const { content, data } = matter(fileContents);
      
      return {
        content: marked(content),
        data,
        filePath,
      };
    })
  );

  return markdownFiles.filter(Boolean) as MarkdownFile[];
}

export async function getMarkdownFile(filePath: string): Promise<MarkdownFile | null> {
  try {
    const fullPath = path.join(contentDir, filePath);
    const fileContents = fs.readFileSync(fullPath, 'utf8');
    const { content, data } = matter(fileContents);
    
    return {
      content: marked(content),
      data,
      filePath,
    };
  } catch (error) {
    console.error(`Error reading markdown file ${filePath}:`, error);
    return null;
  }
}
