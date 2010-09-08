package test.util;

import org.junit.*;
import static org.junit.Assert.*;

import java.util.HashSet;

public class HashSetTest {
	@Test
	public void testEmpty() {
		HashSet<String> s = new HashSet<String>();
		assertTrue(s.isEmpty());
		s.add("foo");
		assertFalse(s.isEmpty());
	}
}

