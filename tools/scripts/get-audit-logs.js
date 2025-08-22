const { PrismaClient } = require('@prisma/client');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables silently
dotenv.config({ path: path.resolve(__dirname, '../../.env'), silent: true });

const prisma = new PrismaClient();

async function getAuditLogs() {
  try {
    const limit = parseInt(process.argv[2]) || 10;
    
    const logs = await prisma.auditLog.findMany({
      take: limit,
      orderBy: {
        createdAt: 'desc'
      },
      include: {
        user: {
          select: {
            id: true,
            username: true,
            fullName: true
          }
        }
      }
    });
    
    // Only output the JSON result
    // Convert BigInt to regular numbers for JSON serialization
    const serializedLogs = logs.map(log => ({
      ...log,
      id: Number(log.id) // Convert BigInt to Number
    }));
    
    process.stdout.write(JSON.stringify({
      success: true,
      data: serializedLogs
    }));
    
  } catch (error) {
    process.stdout.write(JSON.stringify({
      success: false,
      error: error.message
    }));
  } finally {
    await prisma.$disconnect();
  }
}

getAuditLogs();
