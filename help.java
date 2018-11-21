import java.io.*;
import java.math.*;
import java.security.*;
import java.text.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.regex.*;
import java.util.stream.*;
import static java.util.stream.Collectors.joining;
import static java.util.stream.Collectors.toList;



class Result {

    /*
     * Complete the 'primeQuery' function below.
     *
     * The function is expected to return an INTEGER_ARRAY.
     * The function accepts following parameters:
     *  1. INTEGER n
     *  2. INTEGER_ARRAY first
     *  3. INTEGER_ARRAY second
     *  4. INTEGER_ARRAY values
     *  5. INTEGER_ARRAY queries
     */

    public static List<Integer> primeQuery(int n, List<Integer> first, List<Integer> second, List<Integer> values, List<Integer> queries) {
    // Write your code here
		ArrayList<HashSet<Integer>> edges = new ArrayList<HashSet<Integer>>();
		ArrayList<HashSet<Integer>> directChildren = new ArrayList<HashSet<Integer>>();
		ArrayList<HashSet<Integer>> subTrees = new ArrayList<HashSet<Integer>>();
		int[] primeDP = new int[n];
		for(int i=0; i<n; i++){
			edges.add(new HashSet<Integer>());
			directChildren.add(new HashSet<Integer>());
			subTrees.add(new HashSet<Integer>());
			primeDP[i] = -1;
		}

		//Create graph edges in the form of adjacency lists
		for(int i=0; i<first.size(); i++){
			edges.get(first.get(i)-1).add(second.get(i));
			edges.get(second.get(i)-1).add(first.get(i));
		}
		HashSet<Integer> inTree = new HashSet<Integer>();
		inTree.add(1);
		HashSet<Integer> adjacent = edges.get(0);

		//Create list so that each node's adjacency list maps to its DIRECT children
		getDirectChildren(adjacent, directChildren, inTree, 1, edges, n);

		System.out.println(directChildren);

		//Get the number of primes from each query and append it the the following
		ArrayList<Integer> numberOfPrimes = new ArrayList<Integer>();
		for(int q : queries) {
			if(primeDP[q-1] == -1) {
				int numPrimes = getPrimes(numberOfPrimes, directChildren, q, values);
				primeDP[q-1] = numPrimes;
			}
			numberOfPrimes.add(primeDP[q-1]);
		}



		return numberOfPrimes;
	}

	public static int getPrimes(ArrayList<Integer> numberOfPrimes, ArrayList<HashSet<Integer>> directChildren,
								int node, List<Integer> values){
		int primeCounter = 0;
		if (isPrime(values.get(node-1))) {
			primeCounter++;
		}

		for (int i : directChildren.get(node - 1)) {
			if(isPrime(values.get(i-1))) {
				primeCounter++;
			}
		}
		return primeCounter;

	}

	public static boolean isPrime(int primeCheck){
		if(primeCheck == 2) {
			return true;
		}
		if(primeCheck % 2 == 0 || primeCheck == 1) {
			return false;
		}
		for(int i=3; i*i<=primeCheck; i+=2){
			if(primeCheck%i == 0) {
				return false;
			}
		}

		return true;
	}


	public static HashSet<Integer> getDirectChildren(HashSet<Integer> adjacent, ArrayList<HashSet<Integer>> directChildren, 																	HashSet<Integer> inTree, int node, ArrayList<HashSet<Integer>> edges, 																	int numNodes)	{
		if(adjacent.size() == 0){
			return new HashSet<Integer>();
		}
		HashSet<Integer> newSet = new HashSet<Integer>();
		for(int i : adjacent){
			if(!inTree.contains(i)) {
				inTree.add(i);
				newSet.add(i);
				newSet.addAll(getDirectChildren(edges.get(i-1), directChildren, inTree, i, edges, numNodes));
			}
		}
		directChildren.get(node-1).addAll(newSet);
		System.out.println(directChildren);
		return newSet;
	}

}

public class Solution {