package com.deuteriumix.epcfix;
import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import net.minecraft.core.BlockPos;
import net.minecraft.CrashReport;
import net.minecraft.ReportedException;
import net.minecraft.world.level.WorldGenLevel;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class BiomeLookupTest {
    @org.junit.jupiter.api.BeforeAll static void initializeGameVersion() {
        net.minecraft.SharedConstants.tryDetectVersion();
    }
    WorldGenLevel level(RuntimeException failure, AtomicReference<int[]> args, AtomicInteger calls) {
        return (WorldGenLevel)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{WorldGenLevel.class},(p,m,a)->{
            if (m.getName().equals("getBiome")) { if(failure!=null) throw failure; return null; }
            if (m.getName().equals("getUncachedNoiseBiome")) { calls.incrementAndGet(); args.set(new int[]{(int)a[0],(int)a[1],(int)a[2]}); return null; }
            throw new AssertionError(m.getName());
        });
    }
    @Test void keepsNormalLookup() {
        var calls=new AtomicInteger();BiomeLookup.get(level(null,new AtomicReference<>(),calls),new BlockPos(3,80,9));assertEquals(0,calls.get());
    }
    @Test void recoversKnownFailureWithCorrectNegativeQuartCoordinates() {
        var args=new AtomicReference<int[]>();var calls=new AtomicInteger();
        BiomeLookup.get(level(new IllegalStateException("Requested chunk unavailable during world generation"),args,calls),new BlockPos(-1,103,-17));
        assertArrayEquals(new int[]{-1,25,-5},args.get());assertEquals(1,calls.get());
    }
    @Test void doesNotHideOtherFailures() {
        var failure=new IllegalStateException("Different worldgen bug");var calls=new AtomicInteger();
        assertSame(failure,assertThrows(IllegalStateException.class,()->BiomeLookup.get(level(failure,new AtomicReference<>(),calls),BlockPos.ZERO)));assertEquals(0,calls.get());
    }
    @Test void recoversActualWorldGenRegionCrashReport() {
        var args=new AtomicReference<int[]>();var calls=new AtomicInteger();
        var failure=new ReportedException(CrashReport.forThrowable(
                new IllegalStateException("Requested chunk unavailable during world generation"),
                "Exception generating new chunk"));
        BiomeLookup.get(level(failure,args,calls),new BlockPos(-1,103,-17));
        assertArrayEquals(new int[]{-1,25,-5},args.get());assertEquals(1,calls.get());
    }
    @Test void doesNotHideUnrelatedCrashReports() {
        var calls=new AtomicInteger();
        var failure=new ReportedException(CrashReport.forThrowable(new IllegalStateException("Other bug"),"Exception generating new chunk"));
        assertSame(failure,assertThrows(ReportedException.class,()->BiomeLookup.get(level(failure,new AtomicReference<>(),calls),BlockPos.ZERO)));
        assertEquals(0,calls.get());
    }
}
