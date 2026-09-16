package com.deuteriumix.epcfix;
import java.util.concurrent.atomic.AtomicInteger;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.biome.Biome;
import com.mojang.logging.LogUtils;

public final class BiomeLookup {
    private static final AtomicInteger FALLBACKS = new AtomicInteger();
    public static Holder<Biome> get(WorldGenLevel level, BlockPos pos) {
        try {
            return level.getBiome(pos);
        } catch (IllegalStateException error) {
            if (!"Requested chunk unavailable during world generation".equals(error.getMessage())) throw error;
            // Noise biome sampling uses quart coordinates, not block coordinates.
            var biome = level.getUncachedNoiseBiome(QuartPos.fromBlock(pos.getX()),
                    QuartPos.fromBlock(pos.getY()), QuartPos.fromBlock(pos.getZ()));
            if (FALLBACKS.incrementAndGet() <= 3)
                LogUtils.getLogger().info("D9_EPC_BIOME_FALLBACK recovered boundary lookup at {}", pos);
            return biome;
        }
    }
}
