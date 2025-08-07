// Frontend Email Service for FairMind
// This service handles email operations from the frontend

export interface EmailData {
  to: string;
  subject: string;
  body: string;
  htmlBody?: string;
  from?: string;
}

export interface NotificationData {
  to: string;
  type: string;
  message: string;
  additionalData?: Record<string, any>;
}

export interface AlertData {
  to: string;
  alertType: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  timestamp: string;
}

class EmailService {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async sendEmail(emailData: EmailData): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/email/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Failed to send email:', error);
      return false;
    }
  }

  async sendNotification(notificationData: NotificationData): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/email/notification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(notificationData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Failed to send notification:', error);
      return false;
    }
  }

  async sendAlert(alertData: AlertData): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/email/alert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(alertData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Failed to send alert:', error);
      return false;
    }
  }

  // Client-side email validation
  validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // Generate email templates
  generateWelcomeEmail(userName: string, userEmail: string): EmailData {
    return {
      to: userEmail,
      subject: 'Welcome to FairMind - AI Governance Platform',
      body: `Welcome ${userName} to FairMind! We're excited to have you on board.`,
      htmlBody: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background-color: #1f2937; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">Welcome to FairMind</h1>
            <p style="margin: 5px 0 0 0;">AI Governance Platform</p>
          </div>
          
          <div style="padding: 20px; background-color: #f9fafb;">
            <h2 style="color: #374151;">Welcome ${userName}!</h2>
            <p style="color: #6b7280; line-height: 1.6;">
              Thank you for joining FairMind, the comprehensive AI governance platform designed to help you 
              test, monitor, and ensure ethical AI deployment.
            </p>
            
            <div style="background-color: #eff6ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
              <h3 style="margin: 0 0 10px 0; color: #1e40af;">What you can do with FairMind:</h3>
              <ul style="color: #1e40af; margin: 0; padding-left: 20px;">
                <li>Monitor AI model performance in real-time</li>
                <li>Track compliance with NIST AI Risk Management Framework</li>
                <li>Detect bias and fairness issues</li>
                <li>Generate comprehensive governance reports</li>
                <li>Set up automated alerts and notifications</li>
              </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
              <a href="${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}" 
                 style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Get Started
              </a>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
              <p style="color: #9ca3af; font-size: 14px;">
                If you have any questions, please contact support@fairmind.xyz<br>
                We're here to help you succeed with AI governance.
              </p>
            </div>
          </div>
        </div>
      `
    };
  }

  generateComplianceReportEmail(userEmail: string, reportData: any): EmailData {
    return {
      to: userEmail,
      subject: 'FairMind - AI Compliance Report Generated',
      body: `Your AI compliance report has been generated successfully.`,
      htmlBody: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background-color: #1f2937; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">AI Compliance Report</h1>
            <p style="margin: 5px 0 0 0;">FairMind AI Governance Platform</p>
          </div>
          
          <div style="padding: 20px; background-color: #f9fafb;">
            <h2 style="color: #374151;">Compliance Report Generated</h2>
            <p style="color: #6b7280; line-height: 1.6;">
              Your AI compliance report has been generated successfully. Here's a summary of the key findings:
            </p>
            
            <div style="background-color: #f0fdf4; padding: 15px; border-radius: 5px; margin: 20px 0;">
              <h3 style="margin: 0 0 10px 0; color: #166534;">Key Metrics:</h3>
              <ul style="color: #166534; margin: 0; padding-left: 20px;">
                <li>NIST Compliance Score: ${reportData.nistScore || 'N/A'}%</li>
                <li>Active Models: ${reportData.activeModels || 'N/A'}</li>
                <li>Critical Risks: ${reportData.criticalRisks || 'N/A'}</li>
                <li>LLM Safety Score: ${reportData.safetyScore || 'N/A'}%</li>
              </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
              <a href="${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/reports" 
                 style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                View Full Report
              </a>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
              <p style="color: #9ca3af; font-size: 14px;">
                This report was generated automatically by FairMind AI Governance Platform.<br>
                For questions about this report, contact support@fairmind.xyz
              </p>
            </div>
          </div>
        </div>
      `
    };
  }
}

// Export singleton instance
export const emailService = new EmailService(); 