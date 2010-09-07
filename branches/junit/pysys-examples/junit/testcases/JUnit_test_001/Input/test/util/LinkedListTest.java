package test.util;

import org.junit.*;
import static org.junit.Assert.*;

import java.util.LinkedList;

public class LinkedListTest {
	@Test
	public void testStack() {
		LinkedList<Integer> l = new LinkedList<Integer>();
		for(int i = 0; i < 10; i++) {
			l.push(new Integer(i));
		}
		for(int i = 9; i >= 0; i--) {
			assertEquals(i, l.pop().intValue());
		}
	}
}
