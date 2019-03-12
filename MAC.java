import java.security.*;
import java.util.Date;
import java.util.Random;

import javax.crypto.*;
import javax.crypto.spec.SecretKeySpec;

public class MAC{
	public String generateKey() {
	 final String alphabet = "0123456789ABCDE";
	    final int N = alphabet.length();

	    Random r = new Random();

	    for (int i = 0; i < 50; i++) {
	        System.out.print(alphabet.charAt(r.nextInt(N)));
	    }
		return null;
	} 
	public static void main(String args[]) throws NoSuchAlgorithmException, InvalidKeyException{
		String mensaje = "1002755892 647621034 267";
		String mac = "0c7d41633825604a643639ecd0fd5450750ec955";
		try {
			int i=0;
			Date date = new Date();
			while (true) {
				Mac mac1;
//				KeyGenerator kg;
				mac1 = Mac.getInstance("HmacSHA256");
//				kg = KeyGenerator.getInstance("HmacSHA256");
//				kg.init(32);
				byte[] b = new byte[4];
				SecureRandom.getInstanceStrong().nextBytes(b);
				SecretKey clave = new SecretKeySpec(b, "SHA-256");
				mac1.init(clave);
				mac1.update(mensaje.getBytes());
				byte[] s = mac1.doFinal();
				System.out.println("Probando "+s);
				if (i%10000==0) {
					System.out.println("Iteración nº "+i);
				}
				if (s == mac.getBytes()){
					System.out.println("La clave es: "+s);
					System.out.println("La clave es: "+new String(s));
					System.out.println("Time :"+new Date(new Date().getTime()-date.getTime()));
					break;
				}
				i++;
			}
		} catch (NoSuchAlgorithmException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}

