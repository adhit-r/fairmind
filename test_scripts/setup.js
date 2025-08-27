#!/usr/bin/env bun
/**
 * FairMind Testing Setup Script
 * Sets up the testing environment using UV for Python and Bun for JavaScript
 */

import { spawn } from 'child_process';
import chalk from 'chalk';
import ora from 'ora';
import fs from 'fs-extra';
import path from 'path';

class TestingSetup {
  constructor() {
    this.projectRoot = process.cwd();
    this.testDir = path.join(this.projectRoot, 'test_scripts');
  }

  async runCommand(command, args, options = {}) {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        stdio: 'inherit',
        shell: true,
        ...options
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Command failed with exit code ${code}`));
        }
      });

      child.on('error', (error) => {
        reject(error);
      });
    });
  }

  async checkUV() {
    const spinner = ora('Checking UV installation...').start();
    
    try {
      await this.runCommand('uv', ['--version'], { stdio: 'pipe' });
      spinner.succeed('✅ UV is installed');
      return true;
    } catch (error) {
      spinner.fail('❌ UV is not installed');
      console.log(chalk.yellow('Please install UV: https://docs.astral.sh/uv/getting-started/installation/'));
      return false;
    }
  }

  async checkBun() {
    const spinner = ora('Checking Bun installation...').start();
    
    try {
      await this.runCommand('bun', ['--version'], { stdio: 'pipe' });
      spinner.succeed('✅ Bun is installed');
      return true;
    } catch (error) {
      spinner.fail('❌ Bun is not installed');
      console.log(chalk.yellow('Please install Bun: https://bun.sh/docs/installation'));
      return false;
    }
  }

  async installPythonDependencies() {
    const spinner = ora('Installing Python dependencies with UV...').start();
    
    try {
      const requirementsPath = path.join(this.testDir, 'requirements.txt');
      
      if (await fs.pathExists(requirementsPath)) {
        await this.runCommand('uv', ['pip', 'install', '-r', requirementsPath]);
        spinner.succeed('✅ Python dependencies installed with UV');
        return true;
      } else {
        spinner.warn('⚠️  No requirements.txt found, installing basic packages');
        await this.runCommand('uv', ['pip', 'install', 'pandas', 'numpy', 'scikit-learn', 'requests']);
        spinner.succeed('✅ Basic Python packages installed');
        return true;
      }
    } catch (error) {
      spinner.fail(`❌ Failed to install Python dependencies: ${error.message}`);
      return false;
    }
  }

  async installJavaScriptDependencies() {
    const spinner = ora('Installing JavaScript dependencies with Bun...').start();
    
    try {
      const packagePath = path.join(this.testDir, 'package.json');
      
      if (await fs.pathExists(packagePath)) {
        await this.runCommand('bun', ['install'], { cwd: this.testDir });
        spinner.succeed('✅ JavaScript dependencies installed with Bun');
        return true;
      } else {
        spinner.warn('⚠️  No package.json found, installing basic packages');
        await this.runCommand('bun', ['add', 'axios', 'chalk', 'ora', 'fs-extra'], { cwd: this.testDir });
        spinner.succeed('✅ Basic JavaScript packages installed');
        return true;
      }
    } catch (error) {
      spinner.fail(`❌ Failed to install JavaScript dependencies: ${error.message}`);
      return false;
    }
  }

  async setupKaggle() {
    const spinner = ora('Setting up Kaggle API...').start();
    
    try {
      // Install Kaggle CLI with UV
      await this.runCommand('uv', ['pip', 'install', 'kaggle']);
      
      // Check if credentials exist
      const kaggleDir = path.join(process.env.HOME || process.env.USERPROFILE, '.kaggle');
      const kaggleFile = path.join(kaggleDir, 'kaggle.json');
      
      if (await fs.pathExists(kaggleFile)) {
        spinner.succeed('✅ Kaggle credentials found');
        return true;
      } else {
        spinner.warn('⚠️  Kaggle credentials not found');
        console.log(chalk.yellow('\n📋 To set up Kaggle credentials:'));
        console.log(chalk.yellow('1. Go to https://www.kaggle.com/settings/account'));
        console.log(chalk.yellow('2. Scroll down to "API" section'));
        console.log(chalk.yellow('3. Click "Create New API Token"'));
        console.log(chalk.yellow('4. Download kaggle.json'));
        console.log(chalk.yellow(`5. Place it in: ${kaggleDir}`));
        return false;
      }
    } catch (error) {
      spinner.fail(`❌ Failed to setup Kaggle: ${error.message}`);
      return false;
    }
  }

  async createTestDirectories() {
    const spinner = ora('Creating test directories...').start();
    
    try {
      const directories = [
        'test_models/traditional_ml/credit_risk',
        'test_models/traditional_ml/healthcare',
        'test_models/traditional_ml/hiring',
        'test_models/llm_models/text_generation',
        'test_models/llm_models/image_classification',
        'test_models/llm_models/audio_speech',
        'test_models/datasets/raw',
        'test_models/datasets/processed',
        'test_results/bias_analysis',
        'test_results/security_reports',
        'test_results/ethics_evaluations',
        'test_results/ai_bom_reports'
      ];

      for (const dir of directories) {
        await fs.ensureDir(path.join(this.projectRoot, dir));
      }

      spinner.succeed(`✅ Created ${directories.length} test directories`);
      return true;
    } catch (error) {
      spinner.fail(`❌ Failed to create directories: ${error.message}`);
      return false;
    }
  }

  async setupEnvironment() {
    const spinner = ora('Setting up environment variables...').start();
    
    try {
      const envContent = `# FairMind Testing Environment Variables
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8001
NODE_ENV=test
PYTHONPATH=${this.projectRoot}

# Testing Configuration
TEST_TIMEOUT=30000
TEST_RETRIES=3
LOG_LEVEL=info
`;

      const envPath = path.join(this.projectRoot, '.env.test');
      await fs.writeFile(envPath, envContent);
      
      spinner.succeed('✅ Environment variables configured');
      return true;
    } catch (error) {
      spinner.fail(`❌ Failed to setup environment: ${error.message}`);
      return false;
    }
  }

  async runSetup() {
    console.log(chalk.blue.bold('\n🚀 FairMind Testing Environment Setup'));
    console.log(chalk.gray('='.repeat(50)));

    const results = {
      uv: await this.checkUV(),
      bun: await this.checkBun(),
      pythonDeps: false,
      jsDeps: false,
      kaggle: false,
      directories: false,
      environment: false
    };

    if (results.uv) {
      results.pythonDeps = await this.installPythonDependencies();
      results.kaggle = await this.setupKaggle();
    }

    if (results.bun) {
      results.jsDeps = await this.installJavaScriptDependencies();
    }

    results.directories = await this.createTestDirectories();
    results.environment = await this.setupEnvironment();

    this.printSetupSummary(results);
  }

  printSetupSummary(results) {
    console.log(chalk.blue.bold('\n📊 Setup Summary'));
    console.log(chalk.gray('='.repeat(30)));

    const status = {
      'UV (Python)': results.uv ? '✅' : '❌',
      'Bun (JavaScript)': results.bun ? '✅' : '❌',
      'Python Dependencies': results.pythonDeps ? '✅' : '❌',
      'JavaScript Dependencies': results.jsDeps ? '✅' : '❌',
      'Kaggle Setup': results.kaggle ? '✅' : '⚠️',
      'Test Directories': results.directories ? '✅' : '❌',
      'Environment Variables': results.environment ? '✅' : '❌'
    };

    Object.entries(status).forEach(([item, icon]) => {
      console.log(`${icon} ${item}`);
    });

    const successCount = Object.values(results).filter(Boolean).length;
    const totalCount = Object.keys(results).length;
    const successRate = (successCount / totalCount * 100).toFixed(1);

    console.log(chalk.gray('\n' + '='.repeat(30)));
    console.log(`Overall Success Rate: ${chalk.cyan(successRate)}%`);

    if (successRate >= 80) {
      console.log(chalk.green('\n🎉 Setup completed successfully!'));
      console.log(chalk.yellow('\nNext steps:'));
      console.log('1. Run: bun run test:frontend');
      console.log('2. Run: python test_scripts/setup_kaggle.py');
      console.log('3. Run: python test_scripts/train_traditional_models.py');
      console.log('4. Run: python test_scripts/comprehensive_fairmind_test.py');
    } else {
      console.log(chalk.red('\n⚠️  Setup incomplete. Please fix the issues above.'));
    }
  }
}

// Run setup if this file is executed directly
if (import.meta.main) {
  const setup = new TestingSetup();
  setup.runSetup().catch(console.error);
}

export default TestingSetup;
