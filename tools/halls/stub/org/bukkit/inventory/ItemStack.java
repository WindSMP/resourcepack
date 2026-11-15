package org.bukkit.inventory;
/** Headless stand-in: item icons are not part of the hall pictures, only their constructors run in static initialisers. */
public class ItemStack implements Cloneable {
    public final org.bukkit.Material type; public int amount;
    public ItemStack(org.bukkit.Material type) { this(type, 1); }
    public ItemStack(org.bukkit.Material type, int amount) { this.type = type; this.amount = amount; }
    public ItemStack clone() { return new ItemStack(type, amount); }
}
