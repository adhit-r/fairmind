# How to Optimize Issues for Contributors

This guide provides templates and best practices for creating GitHub issues that attract contributors.

## 🎯 Best Practices

1.  **Use Good First Issue Label**: Always label suitable beginner tasks with `good first issue` and `help wanted`.
2.  **Be Explicit**: Assume the contributor knows nothing about the codebase.
3.  **Provide Context**: Explain *why* this change is needed.
4.  **Point to Code**: Include links to relevant files (e.g., `src/components/MyComponent.tsx`).
5.  **Use Checklists**: Break down the task into small, checkable items.

## 📋 Copy-Paste Templates

### 1. Refactoring Task

```markdown
**Context**:
The current implementation of `[Component/Function]` in `[File Path]` is complex and hard to read. We want to refactor it to improve readability and performance.

**Goal**:
Refactor `[Function Name]` to use `[New Approach/Pattern]`.

**Steps**:
- [ ] Locate `[File Path]`
- [ ] Understand the current logic of `[Function]`
- [ ] Extract `[Part of logic]` into a separate helper function
- [ ] Add unit tests for the new helper function
- [ ] Verify that existing tests still pass

**Resources**:
- [Link to similar refactor PR]
- [Documentation on Pattern]
```

### 2. Adding a Test

```markdown
**Context**:
We have low test coverage for `[Component/Service]` in `[File Path]`. We need to ensure this critical path is tested.

**Goal**:
Add unit validation tests for `[Function Name]`.

**Steps**:
- [ ] Create a new test file `[Test File Path]`
- [ ] Write a test case for success scenario
- [ ] Write a test case for failure scenario (e.g., invalid input)
- [ ] Run tests with `uv run pytest` (Backend) or `bun test` (Frontend)

**Resources**:
- See existing tests in `[Reference Test File]`
```

### 3. Documentation Update

```markdown
**Context**:
The documentation for `[Feature]` is outdated or missing.

**Goal**:
Update `docs/[File].md` to reflect the current state of the code.

**Steps**:
- [ ] Read the code in `[File Path]` to understand current behavior
- [ ] Update `docs/[File].md` with new parameters/examples
- [ ] Add a code example showing how to use the feature

**Resources**:
- [Link to source code]
```

## 🔍 Finding "Good First Issues"

Run these commands to find simple tasks in the codebase:

```bash
# Find TODOs that might be good tasks
grep -r "TODO" .

# Find components without tests (rough check)
find apps/frontend/src/components -name "*.tsx" | xargs -I {} sh -c 'if [ ! -f "${0%.tsx}.test.tsx" ]; then echo "Missing test: $0"; fi' {}
```
