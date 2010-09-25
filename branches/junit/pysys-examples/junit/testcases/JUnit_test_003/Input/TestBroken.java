import org.junit.*;
import static org.junit.Assert.*;

import static totest.Broken.*;

public class TestBroken {
	@Test
	public void testAddOne() {
		// This happens to work, but by accident
		assertEquals(brokenAdder(5,1), 6);
	}

	@Test
	public void testAddTwo() {
		// This should fail
		assertEquals(brokenAdder(3,2), 5);
	}
}
