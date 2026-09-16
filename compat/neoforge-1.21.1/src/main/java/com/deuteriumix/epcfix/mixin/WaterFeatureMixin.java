package com.deuteriumix.epcfix.mixin;
import com.deuteriumix.epcfix.BiomeLookup;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.feature.LakeFeature;
import net.minecraft.world.level.levelgen.feature.SnowAndFreezeFeature;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin({LakeFeature.class, SnowAndFreezeFeature.class})
public class WaterFeatureMixin {
    @Redirect(method="place", at=@At(value="INVOKE",
            target="Lnet/minecraft/world/level/WorldGenLevel;getBiome(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/core/Holder;"))
    private Holder<Biome> d9$biomeLookup(WorldGenLevel level, BlockPos pos) {
        return BiomeLookup.get(level, pos);
    }
}
