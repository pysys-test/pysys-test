import org.junit.*;
import static org.junit.Assert.*;

import static totest.Factorial.factorial;

public class TestFactorial {
	@Test
	public void testFactorial() {
		assertEquals(factorial(0), 1);
		assertEquals(factorial(1), 1);
		assertEquals(factorial(5), 120);
	}

	@Test(expected=ArithmeticException.class)
	public void testNegativeFactorial() {
		factorial(-1);
	}
}
