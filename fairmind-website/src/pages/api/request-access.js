export async function POST({ request }) {
  try {
    const formData = await request.formData();
    
    // Extract form data
    const firstName = formData.get('firstName');
    const lastName = formData.get('lastName');
    const email = formData.get('email');
    const company = formData.get('company');
    const jobTitle = formData.get('jobTitle');
    const useCase = formData.get('useCase');
    const teamSize = formData.get('teamSize');
    const message = formData.get('message');
    
    // Create email content
    const emailSubject = `New Access Request: ${firstName} ${lastName} from ${company}`;
    const emailBody = `
New Access Request from Fairmind Website

Name: ${firstName} ${lastName}
Email: ${email}
Company: ${company}
Job Title: ${jobTitle || 'Not specified'}
Primary Use Case: ${useCase || 'Not specified'}
Team Size: ${teamSize || 'Not specified'}

Additional Information:
${message || 'No additional information provided'}

---
This request was submitted from the Fairmind website contact form.
    `.trim();
    
    // Send email using Formspree (you'll need to configure this)
    const formspreeResponse = await fetch('https://formspree.io/f/xayzqjqw', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        _subject: emailSubject,
        _replyto: email,
        name: `${firstName} ${lastName}`,
        email: email,
        company: company,
        jobTitle: jobTitle,
        useCase: useCase,
        teamSize: teamSize,
        message: message,
        _to: 'support@fairmind.xyz'
      })
    });
    
    if (formspreeResponse.ok) {
      return new Response(JSON.stringify({ 
        success: true, 
        message: 'Thank you! We\'ll get back to you within 24 hours.' 
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } else {
      throw new Error('Failed to send email');
    }
    
  } catch (error) {
    console.error('Error processing form submission:', error);
    return new Response(JSON.stringify({ 
      success: false, 
      message: 'Sorry, there was an error. Please try again or contact us directly.' 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
