# E2E Test: Interest Form and Landing Page

Test the landing page and initial user interest flow for the AI Course Platform.

## User Story

As a prospective AI student
I want to view the course landing page and understand what the platform offers
So that I can decide whether to register for the AI learning sessions

## Test Steps

1. Navigate to the Application URL (`http://localhost:5173`)
2. Take a screenshot of the initial state
3. **Verify** the page title/heading displays "AI in 4"
4. **Verify** the tagline "Humanizing the Machine" is visible
5. **Verify** core landing page elements are present:
   - "Get Started" button
   - "Sign In" button
   - "Expert-Led Sessions" feature card
   - "Practical Projects" feature card
   - "Community Support" feature card
6. **Verify** "What You'll Learn" section is visible
7. **Verify** learning topics are displayed:
   - "Fundamentals of AI and Machine Learning"
   - "Building AI-Powered Applications"
   - "Working with Large Language Models"
   - "Ethical AI and Best Practices"
8. Take a screenshot of the features section
9. Click "Get Started" button
10. **Verify** navigation to `/register` page occurs
11. Take a screenshot of the registration page

## Success Criteria

- Landing page displays correctly with "AI in 4" branding
- All feature cards are visible and properly formatted
- Learning topics section is present
- "Get Started" button navigates to registration page
- "Sign In" button is accessible
- Page is responsive and visually correct
- 3 screenshots are captured
