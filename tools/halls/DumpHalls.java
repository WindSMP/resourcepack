import java.lang.reflect.*;
import java.nio.file.*;
import org.bukkit.plugin.Plugin;

/** Runs the prototype's HallArt registration (same order as GoliathModule.enable) and writes HallArt.buildPack(). */
public class DumpHalls {
    static Object holder(Class<?> c) throws Exception {
        try { return c.getField("Companion").get(null); } catch (NoSuchFieldException e) { return c.getField("INSTANCE").get(null); }
    }
    public static void main(String[] a) throws Exception {
        ClassLoader cl = DumpHalls.class.getClassLoader();
        Plugin plugin = (Plugin) Proxy.newProxyInstance(cl, new Class[]{Plugin.class}, (p, m, args) -> switch (m.getName()) {
            case "getResource" -> cl.getResourceAsStream((String) args[0]);
            case "getLogger" -> java.util.logging.Logger.getLogger("dump");
            case "getName" -> "DialogStore";
            case "toString" -> "DumpPlugin";
            case "hashCode" -> 1;
            case "equals" -> p == args[0];
            default -> { if (m.getReturnType() == boolean.class) yield false; yield null; }
        });
        String[] order = {"me.goliath.DemoScene", "me.goliath.settings.SettingsScene", "me.goliath.stats.StatsScene",
            "me.goliath.leaderboard.LeaderboardScene", "me.goliath.welcome.WelcomeScene", "me.goliath.welcome.RulesScene",
            "me.goliath.welcome.MediaScene", "me.goliath.rtp.RtpScene", "me.goliath.welcome.StoreScene", "me.goliath.crate.CrateScene"};
        for (String n : order) {
            Object h = holder(Class.forName(n));
            Method r = null;
            for (Method m : h.getClass().getMethods()) if (m.getName().equals("register")) r = m;
            r.invoke(h, r.getParameterCount() == 0 ? new Object[0] : new Object[]{plugin});
            System.err.println("registered " + n);
        }
        Object art = Class.forName("me.goliath.scene.HallArt").getField("INSTANCE").get(null);
        byte[] zip = (byte[]) art.getClass().getMethod("buildPack").invoke(art);
        Files.write(Path.of(a[0]), zip);
        System.err.println("wrote " + zip.length + " bytes");
    }
}
