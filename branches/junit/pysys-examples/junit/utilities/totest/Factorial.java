package totest;

public class Factorial {
	public static long factorial(long n) {
		if(n < 0) {
			throw new ArithmeticException("Negative argument to factorial");
		} else if(n <= 1) {
			return 1;
		} else {
			return factorial(n - 1) * n;
		}
	}
}
