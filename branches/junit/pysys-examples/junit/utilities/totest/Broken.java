package totest;

public class Broken {

	/**
	 * A function which claims to add two numbers together but actually
	 * doesn't - used to test that the PySys frame will catch failing
	 * JUnit tests.
	 */
	public static int brokenAdder(int x, int y) {
		return x + 1;
	}
}
