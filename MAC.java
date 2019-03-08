import java.security.*
import javax.crypto.*

public class MAC{
	public static void main(String args[]){
		mac1 = Mac.getInstance("HmacSHA256");
		kg = KeyGenerator.getInstance("HmacSHA256");
		SecretKey clave = kf.generateKey();
		
		mac1.init(clave);
	}
}
