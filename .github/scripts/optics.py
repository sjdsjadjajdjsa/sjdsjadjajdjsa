import math

ROOT3 = math.sqrt(3)


def refract(d, n, eta):
    cosi = -(d[0] * n[0] + d[1] * n[1])
    k = 1 - eta * eta * (1 - cosi * cosi)
    c = eta * cosi - math.sqrt(k)
    return (eta * d[0] + c * n[0], eta * d[1] + c * n[1])


def hit(p, d, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = d[0] * ey - d[1] * ex
    t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
    return (p[0] + d[0] * t, p[1] + d[1] * t)


def prism(cx, by, s, f, n_mid, ns):
    h = s * ROOT3 / 2
    a, l, r = (cx, by - h), (cx - s / 2, by), (cx + s / 2, by)
    p = (a[0] + f * (l[0] - a[0]), a[1] + f * (l[1] - a[1]))
    th = math.radians(30) - math.asin(n_mid / 2)
    d0 = (math.cos(th), math.sin(th))
    rays = []
    for n in ns:
        d1 = refract(d0, (-ROOT3 / 2, -0.5), 1 / n)
        q = hit(p, d1, a, r)
        rays.append((q, refract(d1, (-ROOT3 / 2, 0.5), n)))
    return dict(a=a, l=l, r=r, p=p, d0=d0, rays=rays)
