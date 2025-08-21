# GitHub Issue Tracking Guide - FairMind

## 🚀 Quick Commands

### Create Issues
```bash
# Bug report
gh issue create --title "Brief description" --body "Detailed description" --label "bug"

# Feature request
gh issue create --title "Brief description" --body "Detailed description" --label "bug"

# Documentation
gh issue create --title "Brief description" --body "Detailed description" --label "bug"
```

### Manage Issues
```bash
# List all issues
gh issue list

# View specific issue
gh issue view <number>

# Close issue
gh issue close <number> --reason completed

# Add comments
gh issue comment <number> --body "Comment text"
```

## 📋 Current Issues

| ID | Title | Status | Priority |
|----|-------|--------|----------|
| #4 | Create API endpoints for AI BOM service | Open | High |
| #5 | Integrate AI BOM service with database | Open | High |
| #6 | Build AI BOM frontend interface | Open | Medium |
| #7 | Add comprehensive testing for AI BOM service | Open | Medium |

## 🏷️ Labels to Use

### Type Labels
- `bug` - Something isn't working
- `feature` - New functionality
- `enhancement` - Improvements to existing features
- `documentation` - Documentation improvements

### Component Labels
- `ai-bom` - AI Bill of Materials related
- `fairness-analysis` - Fairness analysis features
- `model-registry` - Model registry features
- `frontend` - Frontend related
- `backend` - Backend related

### Priority Labels
- `high-priority` - Critical, needs immediate attention
- `medium-priority` - Important but not urgent
- `low-priority` - Nice to have

## 📝 Issue Templates

### Bug Report Template
```
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: 
- Browser: 
- Version: 

## Additional Context
Any other relevant information
```

### Feature Request Template
```
## Feature Description
Brief description of the new feature

## Use Case
Why is this feature needed?

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Notes
Any technical considerations

## Priority
High/Medium/Low
```

## 🔄 Workflow

1. **Create Issue** - Use `gh issue create` with appropriate labels
2. **Work on Issue** - Reference issue number in commit messages
3. **Update Issue** - Add comments for progress updates
4. **Close Issue** - Use `gh issue close` when complete

## 💡 Best Practices

- Use descriptive titles
- Include reproduction steps for bugs
- Add acceptance criteria for features
- Tag with appropriate labels
- Reference issues in commit messages: `fixes #123` or `closes #123`
- Update issues with progress comments
- Close issues when resolved

## 🎯 Next Steps

1. Start with issue #4 (API endpoints) - highest priority
2. Then issue #5 (database integration)
3. Follow with #6 (frontend interface)
4. Finally #7 (comprehensive testing)
