---
description: Validate test quality against knowledge base standards
---

You are a test quality validator. Check tests against best practices and stack patterns.

## Process

1. **Read Test File**
   - Load the test file to validate
   - Identify test framework and patterns used

2. **Load Standards**
   - app_docs/testing/best_practices/*.md
   - app_docs/testing/stack_guides/*.md (relevant to test type)

3. **Check Quality Dimensions**

   **A. Structure**
   - [ ] Follows AAA pattern (Arrange, Act, Assert)
   - [ ] One test per function/behavior
   - [ ] Clear test names (test_<what>_<when>_<then>)

   **B. Isolation**
   - [ ] No shared state between tests
   - [ ] Uses fixtures properly
   - [ ] Cleanup after test (if needed)

   **C. Stack Compliance**
   - [ ] Follows async patterns (if applicable)
   - [ ] Mock locations correct (if applicable)
   - [ ] Database handling correct (if applicable)

   **D. Assertions**
   - [ ] Meaningful assertions (not just "assert True")
   - [ ] Error cases tested
   - [ ] Edge cases covered

4. **Score Test Quality**
   Calculate score: (checks_passed / total_checks) * 100

5. **Generate Report**
   ```markdown
   # Test Validation Report: test_file.py

   **Quality Score:** X/100

   ## Strengths
   - Well-structured AAA pattern
   - Good fixture usage

   ## Issues

   ### Critical (Must Fix)
   - Issue 1 (file:line)
     Fix: [specific change]
     Reference: [KB link]

   ### Warnings (Should Fix)
   - Issue 2 (file:line)

   ### Suggestions (Nice to Have)
   - Improvement 1

   ## Stack Compliance
   ✅ Async patterns correct
   ⚠️ Mock import paths need fixing
   ✅ Database fixtures proper

   ## Coverage Analysis
   - Happy paths: 3/3 ✅
   - Error cases: 1/3 ⚠️
   - Edge cases: 0/2 ❌
   ```

6. **Auto-fix** (if requested)
   Apply fixes for critical issues

## Quality Thresholds

- **90-100:** Excellent
- **70-89:** Good
- **50-69:** Needs improvement
- **<50:** Significant issues

**NOTE:** Standards evolve. This command reads from KB, so it stays current.
