---
name: "tdd"
description: "Test-Driven Development workflow. Write tests first, then implement code to make them pass. Use when implementing features or fixing bugs."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["testing", "tdd", "development", "quality", "best-practices"]
trigger_patterns:
  - "test first"
  - "tdd"
  - "write tests"
  - "test-driven"
  - "unit test"
---

# Test-Driven Development (TDD) Skill

**CRITICAL**: Write tests BEFORE writing implementation code. This ensures code is testable and meets requirements.

## The TDD Cycle

```
   ┌─────────────────────────────────────┐
   │                                     │
   │   RED → GREEN → REFACTOR → Repeat   │
   │                                     │
   └─────────────────────────────────────┘
```

1. **RED**: Write a failing test that defines expected behavior
2. **GREEN**: Write minimum code to make the test pass
3. **REFACTOR**: Clean up while keeping tests green
4. **Repeat**: Add next test case

## When to Use

Activate TDD when:
- Implementing new features
- Fixing bugs (write test that reproduces bug first)
- Refactoring existing code
- Adding edge case handling

## The TDD Process

### Phase 1: Understand Requirements

Before writing any code:
1. Clarify what the feature should do
2. Identify inputs, outputs, and edge cases
3. List test cases needed

```markdown
## Feature: [Name]
### Happy Path Cases
- [ ] Test case 1: Given X, when Y, then Z
- [ ] Test case 2: Given A, when B, then C

### Edge Cases
- [ ] Empty input
- [ ] Invalid input
- [ ] Boundary values

### Error Cases
- [ ] What should happen when X fails?
```

### Phase 2: RED - Write Failing Test

Write a test that:
1. Describes the expected behavior
2. Fails for the right reason (not implementation exists yet)
3. Is simple and focused

```python
# Python example
def test_calculate_total_with_discount():
    """Should apply 10% discount for orders over $100"""
    order = Order(items=[Item(price=150)])

    result = order.calculate_total()

    assert result == 135.00  # 150 - 10% = 135
```

```javascript
// JavaScript example
describe('calculateTotal', () => {
  it('should apply 10% discount for orders over $100', () => {
    const order = new Order([{ price: 150 }]);

    const result = order.calculateTotal();

    expect(result).toBe(135);
  });
});
```

### Phase 3: GREEN - Make Test Pass

Write the simplest code that makes the test pass:
1. Don't over-engineer
2. Don't add features the test doesn't require
3. It's okay if code is ugly - we'll refactor next

```python
def calculate_total(self):
    total = sum(item.price for item in self.items)
    if total > 100:
        total = total * 0.9  # 10% discount
    return total
```

### Phase 4: REFACTOR - Clean Up

Improve code quality while keeping tests green:
1. Remove duplication
2. Improve naming
3. Extract methods if needed
4. Run tests after each change

```python
DISCOUNT_THRESHOLD = 100
DISCOUNT_RATE = 0.10

def calculate_total(self):
    subtotal = self._calculate_subtotal()
    discount = self._calculate_discount(subtotal)
    return subtotal - discount

def _calculate_subtotal(self):
    return sum(item.price for item in self.items)

def _calculate_discount(self, subtotal):
    if subtotal > DISCOUNT_THRESHOLD:
        return subtotal * DISCOUNT_RATE
    return 0
```

### Phase 5: Repeat

Add the next test case and repeat the cycle.

## Test Patterns

### Arrange-Act-Assert (AAA)

```python
def test_user_creation():
    # Arrange - set up test data
    user_data = {"name": "Alice", "email": "alice@example.com"}

    # Act - perform the action
    user = User.create(user_data)

    # Assert - verify the result
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
```

### Given-When-Then (BDD style)

```python
def test_user_login():
    # Given a registered user
    user = create_user(email="test@example.com", password="secret")

    # When they attempt to login with correct credentials
    result = login(email="test@example.com", password="secret")

    # Then they should be authenticated
    assert result.success == True
    assert result.token is not None
```

## Common Test Types

### Unit Tests
- Test single functions/methods in isolation
- Mock external dependencies
- Fast execution

### Integration Tests
- Test multiple components together
- Use real databases (test instances)
- Slower but more realistic

### End-to-End Tests
- Test full user workflows
- Run against complete system
- Slowest but most comprehensive

## Anti-Patterns to Avoid

- **Test After**: Writing tests after implementation defeats the purpose
- **Testing Implementation**: Test behavior, not implementation details
- **Brittle Tests**: Tests shouldn't break when refactoring
- **Skipping Refactor**: Technical debt accumulates without refactoring
- **Too Many Mocks**: Over-mocking makes tests meaningless

## Example TDD Session

**User**: "Implement a password validator"

**Agent Response**:
> Let me implement this using TDD:
>
> ## Test Cases to Cover
> 1. Password must be at least 8 characters
> 2. Password must contain uppercase letter
> 3. Password must contain number
> 4. Password must contain special character
>
> ## RED: First Test
> ```python
> def test_rejects_short_password():
>     result = validate_password("short")
>     assert result.valid == False
>     assert "at least 8 characters" in result.errors
> ```
>
> ## GREEN: Minimal Implementation
> ```python
> def validate_password(password):
>     errors = []
>     if len(password) < 8:
>         errors.append("Password must be at least 8 characters")
>     return ValidationResult(valid=len(errors) == 0, errors=errors)
> ```
>
> [Continues with next test case...]
