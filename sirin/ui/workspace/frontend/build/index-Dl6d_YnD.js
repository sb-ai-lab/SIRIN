var Ho = { exports: {} }, Nr = {}, Ao = { exports: {} }, G = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Xa;
function df() {
  if (Xa) return G;
  Xa = 1;
  var u = Symbol.for("react.element"), a = Symbol.for("react.portal"), c = Symbol.for("react.fragment"), g = Symbol.for("react.strict_mode"), w = Symbol.for("react.profiler"), x = Symbol.for("react.provider"), z = Symbol.for("react.context"), L = Symbol.for("react.forward_ref"), E = Symbol.for("react.suspense"), k = Symbol.for("react.memo"), U = Symbol.for("react.lazy"), B = Symbol.iterator;
  function J(h) {
    return h === null || typeof h != "object" ? null : (h = B && h[B] || h["@@iterator"], typeof h == "function" ? h : null);
  }
  var ie = { isMounted: function() {
    return !1;
  }, enqueueForceUpdate: function() {
  }, enqueueReplaceState: function() {
  }, enqueueSetState: function() {
  } }, ve = Object.assign, K = {};
  function X(h, S, Z) {
    this.props = h, this.context = S, this.refs = K, this.updater = Z || ie;
  }
  X.prototype.isReactComponent = {}, X.prototype.setState = function(h, S) {
    if (typeof h != "object" && typeof h != "function" && h != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
    this.updater.enqueueSetState(this, h, S, "setState");
  }, X.prototype.forceUpdate = function(h) {
    this.updater.enqueueForceUpdate(this, h, "forceUpdate");
  };
  function b() {
  }
  b.prototype = X.prototype;
  function Ne(h, S, Z) {
    this.props = h, this.context = S, this.refs = K, this.updater = Z || ie;
  }
  var ge = Ne.prototype = new b();
  ge.constructor = Ne, ve(ge, X.prototype), ge.isPureReactComponent = !0;
  var fe = Array.isArray, Te = Object.prototype.hasOwnProperty, ke = { current: null }, pe = { key: !0, ref: !0, __self: !0, __source: !0 };
  function Q(h, S, Z) {
    var Y, ee = {}, ne = null, oe = null;
    if (S != null) for (Y in S.ref !== void 0 && (oe = S.ref), S.key !== void 0 && (ne = "" + S.key), S) Te.call(S, Y) && !pe.hasOwnProperty(Y) && (ee[Y] = S[Y]);
    var re = arguments.length - 2;
    if (re === 1) ee.children = Z;
    else if (1 < re) {
      for (var he = Array(re), tn = 0; tn < re; tn++) he[tn] = arguments[tn + 2];
      ee.children = he;
    }
    if (h && h.defaultProps) for (Y in re = h.defaultProps, re) ee[Y] === void 0 && (ee[Y] = re[Y]);
    return { $$typeof: u, type: h, key: ne, ref: oe, props: ee, _owner: ke.current };
  }
  function Ze(h, S) {
    return { $$typeof: u, type: h.type, key: S, ref: h.ref, props: h.props, _owner: h._owner };
  }
  function We(h) {
    return typeof h == "object" && h !== null && h.$$typeof === u;
  }
  function Je(h) {
    var S = { "=": "=0", ":": "=2" };
    return "$" + h.replace(/[=:]/g, function(Z) {
      return S[Z];
    });
  }
  var ze = /\/+/g;
  function V(h, S) {
    return typeof h == "object" && h !== null && h.key != null ? Je("" + h.key) : S.toString(36);
  }
  function _(h, S, Z, Y, ee) {
    var ne = typeof h;
    (ne === "undefined" || ne === "boolean") && (h = null);
    var oe = !1;
    if (h === null) oe = !0;
    else switch (ne) {
      case "string":
      case "number":
        oe = !0;
        break;
      case "object":
        switch (h.$$typeof) {
          case u:
          case a:
            oe = !0;
        }
    }
    if (oe) return oe = h, ee = ee(oe), h = Y === "" ? "." + V(oe, 0) : Y, fe(ee) ? (Z = "", h != null && (Z = h.replace(ze, "$&/") + "/"), _(ee, S, Z, "", function(tn) {
      return tn;
    })) : ee != null && (We(ee) && (ee = Ze(ee, Z + (!ee.key || oe && oe.key === ee.key ? "" : ("" + ee.key).replace(ze, "$&/") + "/") + h)), S.push(ee)), 1;
    if (oe = 0, Y = Y === "" ? "." : Y + ":", fe(h)) for (var re = 0; re < h.length; re++) {
      ne = h[re];
      var he = Y + V(ne, re);
      oe += _(ne, S, Z, he, ee);
    }
    else if (he = J(h), typeof he == "function") for (h = he.call(h), re = 0; !(ne = h.next()).done; ) ne = ne.value, he = Y + V(ne, re++), oe += _(ne, S, Z, he, ee);
    else if (ne === "object") throw S = String(h), Error("Objects are not valid as a React child (found: " + (S === "[object Object]" ? "object with keys {" + Object.keys(h).join(", ") + "}" : S) + "). If you meant to render a collection of children, use an array instead.");
    return oe;
  }
  function Le(h, S, Z) {
    if (h == null) return h;
    var Y = [], ee = 0;
    return _(h, Y, "", "", function(ne) {
      return S.call(Z, ne, ee++);
    }), Y;
  }
  function Ce(h) {
    if (h._status === -1) {
      var S = h._result;
      S = S(), S.then(function(Z) {
        (h._status === 0 || h._status === -1) && (h._status = 1, h._result = Z);
      }, function(Z) {
        (h._status === 0 || h._status === -1) && (h._status = 2, h._result = Z);
      }), h._status === -1 && (h._status = 0, h._result = S);
    }
    if (h._status === 1) return h._result.default;
    throw h._result;
  }
  var ae = { current: null }, O = { transition: null }, T = { ReactCurrentDispatcher: ae, ReactCurrentBatchConfig: O, ReactCurrentOwner: ke };
  function P() {
    throw Error("act(...) is not supported in production builds of React.");
  }
  return G.Children = { map: Le, forEach: function(h, S, Z) {
    Le(h, function() {
      S.apply(this, arguments);
    }, Z);
  }, count: function(h) {
    var S = 0;
    return Le(h, function() {
      S++;
    }), S;
  }, toArray: function(h) {
    return Le(h, function(S) {
      return S;
    }) || [];
  }, only: function(h) {
    if (!We(h)) throw Error("React.Children.only expected to receive a single React element child.");
    return h;
  } }, G.Component = X, G.Fragment = c, G.Profiler = w, G.PureComponent = Ne, G.StrictMode = g, G.Suspense = E, G.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = T, G.act = P, G.cloneElement = function(h, S, Z) {
    if (h == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + h + ".");
    var Y = ve({}, h.props), ee = h.key, ne = h.ref, oe = h._owner;
    if (S != null) {
      if (S.ref !== void 0 && (ne = S.ref, oe = ke.current), S.key !== void 0 && (ee = "" + S.key), h.type && h.type.defaultProps) var re = h.type.defaultProps;
      for (he in S) Te.call(S, he) && !pe.hasOwnProperty(he) && (Y[he] = S[he] === void 0 && re !== void 0 ? re[he] : S[he]);
    }
    var he = arguments.length - 2;
    if (he === 1) Y.children = Z;
    else if (1 < he) {
      re = Array(he);
      for (var tn = 0; tn < he; tn++) re[tn] = arguments[tn + 2];
      Y.children = re;
    }
    return { $$typeof: u, type: h.type, key: ee, ref: ne, props: Y, _owner: oe };
  }, G.createContext = function(h) {
    return h = { $$typeof: z, _currentValue: h, _currentValue2: h, _threadCount: 0, Provider: null, Consumer: null, _defaultValue: null, _globalName: null }, h.Provider = { $$typeof: x, _context: h }, h.Consumer = h;
  }, G.createElement = Q, G.createFactory = function(h) {
    var S = Q.bind(null, h);
    return S.type = h, S;
  }, G.createRef = function() {
    return { current: null };
  }, G.forwardRef = function(h) {
    return { $$typeof: L, render: h };
  }, G.isValidElement = We, G.lazy = function(h) {
    return { $$typeof: U, _payload: { _status: -1, _result: h }, _init: Ce };
  }, G.memo = function(h, S) {
    return { $$typeof: k, type: h, compare: S === void 0 ? null : S };
  }, G.startTransition = function(h) {
    var S = O.transition;
    O.transition = {};
    try {
      h();
    } finally {
      O.transition = S;
    }
  }, G.unstable_act = P, G.useCallback = function(h, S) {
    return ae.current.useCallback(h, S);
  }, G.useContext = function(h) {
    return ae.current.useContext(h);
  }, G.useDebugValue = function() {
  }, G.useDeferredValue = function(h) {
    return ae.current.useDeferredValue(h);
  }, G.useEffect = function(h, S) {
    return ae.current.useEffect(h, S);
  }, G.useId = function() {
    return ae.current.useId();
  }, G.useImperativeHandle = function(h, S, Z) {
    return ae.current.useImperativeHandle(h, S, Z);
  }, G.useInsertionEffect = function(h, S) {
    return ae.current.useInsertionEffect(h, S);
  }, G.useLayoutEffect = function(h, S) {
    return ae.current.useLayoutEffect(h, S);
  }, G.useMemo = function(h, S) {
    return ae.current.useMemo(h, S);
  }, G.useReducer = function(h, S, Z) {
    return ae.current.useReducer(h, S, Z);
  }, G.useRef = function(h) {
    return ae.current.useRef(h);
  }, G.useState = function(h) {
    return ae.current.useState(h);
  }, G.useSyncExternalStore = function(h, S, Z) {
    return ae.current.useSyncExternalStore(h, S, Z);
  }, G.useTransition = function() {
    return ae.current.useTransition();
  }, G.version = "18.3.1", G;
}
var Za;
function Ko() {
  return Za || (Za = 1, Ao.exports = df()), Ao.exports;
}
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ja;
function ff() {
  if (Ja) return Nr;
  Ja = 1;
  var u = Ko(), a = Symbol.for("react.element"), c = Symbol.for("react.fragment"), g = Object.prototype.hasOwnProperty, w = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, x = { key: !0, ref: !0, __self: !0, __source: !0 };
  function z(L, E, k) {
    var U, B = {}, J = null, ie = null;
    k !== void 0 && (J = "" + k), E.key !== void 0 && (J = "" + E.key), E.ref !== void 0 && (ie = E.ref);
    for (U in E) g.call(E, U) && !x.hasOwnProperty(U) && (B[U] = E[U]);
    if (L && L.defaultProps) for (U in E = L.defaultProps, E) B[U] === void 0 && (B[U] = E[U]);
    return { $$typeof: a, type: L, key: J, ref: ie, props: B, _owner: w.current };
  }
  return Nr.Fragment = c, Nr.jsx = z, Nr.jsxs = z, Nr;
}
var Ka;
function pf() {
  return Ka || (Ka = 1, Ho.exports = ff()), Ho.exports;
}
var o = pf(), ue = Ko(), Ul = {}, Bo = { exports: {} }, en = {}, Xo = { exports: {} }, Zo = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Qa;
function hf() {
  return Qa || (Qa = 1, (function(u) {
    function a(O, T) {
      var P = O.length;
      O.push(T);
      e: for (; 0 < P; ) {
        var h = P - 1 >>> 1, S = O[h];
        if (0 < w(S, T)) O[h] = T, O[P] = S, P = h;
        else break e;
      }
    }
    function c(O) {
      return O.length === 0 ? null : O[0];
    }
    function g(O) {
      if (O.length === 0) return null;
      var T = O[0], P = O.pop();
      if (P !== T) {
        O[0] = P;
        e: for (var h = 0, S = O.length, Z = S >>> 1; h < Z; ) {
          var Y = 2 * (h + 1) - 1, ee = O[Y], ne = Y + 1, oe = O[ne];
          if (0 > w(ee, P)) ne < S && 0 > w(oe, ee) ? (O[h] = oe, O[ne] = P, h = ne) : (O[h] = ee, O[Y] = P, h = Y);
          else if (ne < S && 0 > w(oe, P)) O[h] = oe, O[ne] = P, h = ne;
          else break e;
        }
      }
      return T;
    }
    function w(O, T) {
      var P = O.sortIndex - T.sortIndex;
      return P !== 0 ? P : O.id - T.id;
    }
    if (typeof performance == "object" && typeof performance.now == "function") {
      var x = performance;
      u.unstable_now = function() {
        return x.now();
      };
    } else {
      var z = Date, L = z.now();
      u.unstable_now = function() {
        return z.now() - L;
      };
    }
    var E = [], k = [], U = 1, B = null, J = 3, ie = !1, ve = !1, K = !1, X = typeof setTimeout == "function" ? setTimeout : null, b = typeof clearTimeout == "function" ? clearTimeout : null, Ne = typeof setImmediate < "u" ? setImmediate : null;
    typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
    function ge(O) {
      for (var T = c(k); T !== null; ) {
        if (T.callback === null) g(k);
        else if (T.startTime <= O) g(k), T.sortIndex = T.expirationTime, a(E, T);
        else break;
        T = c(k);
      }
    }
    function fe(O) {
      if (K = !1, ge(O), !ve) if (c(E) !== null) ve = !0, Ce(Te);
      else {
        var T = c(k);
        T !== null && ae(fe, T.startTime - O);
      }
    }
    function Te(O, T) {
      ve = !1, K && (K = !1, b(Q), Q = -1), ie = !0;
      var P = J;
      try {
        for (ge(T), B = c(E); B !== null && (!(B.expirationTime > T) || O && !Je()); ) {
          var h = B.callback;
          if (typeof h == "function") {
            B.callback = null, J = B.priorityLevel;
            var S = h(B.expirationTime <= T);
            T = u.unstable_now(), typeof S == "function" ? B.callback = S : B === c(E) && g(E), ge(T);
          } else g(E);
          B = c(E);
        }
        if (B !== null) var Z = !0;
        else {
          var Y = c(k);
          Y !== null && ae(fe, Y.startTime - T), Z = !1;
        }
        return Z;
      } finally {
        B = null, J = P, ie = !1;
      }
    }
    var ke = !1, pe = null, Q = -1, Ze = 5, We = -1;
    function Je() {
      return !(u.unstable_now() - We < Ze);
    }
    function ze() {
      if (pe !== null) {
        var O = u.unstable_now();
        We = O;
        var T = !0;
        try {
          T = pe(!0, O);
        } finally {
          T ? V() : (ke = !1, pe = null);
        }
      } else ke = !1;
    }
    var V;
    if (typeof Ne == "function") V = function() {
      Ne(ze);
    };
    else if (typeof MessageChannel < "u") {
      var _ = new MessageChannel(), Le = _.port2;
      _.port1.onmessage = ze, V = function() {
        Le.postMessage(null);
      };
    } else V = function() {
      X(ze, 0);
    };
    function Ce(O) {
      pe = O, ke || (ke = !0, V());
    }
    function ae(O, T) {
      Q = X(function() {
        O(u.unstable_now());
      }, T);
    }
    u.unstable_IdlePriority = 5, u.unstable_ImmediatePriority = 1, u.unstable_LowPriority = 4, u.unstable_NormalPriority = 3, u.unstable_Profiling = null, u.unstable_UserBlockingPriority = 2, u.unstable_cancelCallback = function(O) {
      O.callback = null;
    }, u.unstable_continueExecution = function() {
      ve || ie || (ve = !0, Ce(Te));
    }, u.unstable_forceFrameRate = function(O) {
      0 > O || 125 < O ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : Ze = 0 < O ? Math.floor(1e3 / O) : 5;
    }, u.unstable_getCurrentPriorityLevel = function() {
      return J;
    }, u.unstable_getFirstCallbackNode = function() {
      return c(E);
    }, u.unstable_next = function(O) {
      switch (J) {
        case 1:
        case 2:
        case 3:
          var T = 3;
          break;
        default:
          T = J;
      }
      var P = J;
      J = T;
      try {
        return O();
      } finally {
        J = P;
      }
    }, u.unstable_pauseExecution = function() {
    }, u.unstable_requestPaint = function() {
    }, u.unstable_runWithPriority = function(O, T) {
      switch (O) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
          break;
        default:
          O = 3;
      }
      var P = J;
      J = O;
      try {
        return T();
      } finally {
        J = P;
      }
    }, u.unstable_scheduleCallback = function(O, T, P) {
      var h = u.unstable_now();
      switch (typeof P == "object" && P !== null ? (P = P.delay, P = typeof P == "number" && 0 < P ? h + P : h) : P = h, O) {
        case 1:
          var S = -1;
          break;
        case 2:
          S = 250;
          break;
        case 5:
          S = 1073741823;
          break;
        case 4:
          S = 1e4;
          break;
        default:
          S = 5e3;
      }
      return S = P + S, O = { id: U++, callback: T, priorityLevel: O, startTime: P, expirationTime: S, sortIndex: -1 }, P > h ? (O.sortIndex = P, a(k, O), c(E) === null && O === c(k) && (K ? (b(Q), Q = -1) : K = !0, ae(fe, P - h))) : (O.sortIndex = S, a(E, O), ve || ie || (ve = !0, Ce(Te))), O;
    }, u.unstable_shouldYield = Je, u.unstable_wrapCallback = function(O) {
      var T = J;
      return function() {
        var P = J;
        J = T;
        try {
          return O.apply(this, arguments);
        } finally {
          J = P;
        }
      };
    };
  })(Zo)), Zo;
}
var Ga;
function mf() {
  return Ga || (Ga = 1, Xo.exports = hf()), Xo.exports;
}
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ya;
function vf() {
  if (Ya) return en;
  Ya = 1;
  var u = Ko(), a = mf();
  function c(e) {
    for (var n = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, t = 1; t < arguments.length; t++) n += "&args[]=" + encodeURIComponent(arguments[t]);
    return "Minified React error #" + e + "; visit " + n + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
  }
  var g = /* @__PURE__ */ new Set(), w = {};
  function x(e, n) {
    z(e, n), z(e + "Capture", n);
  }
  function z(e, n) {
    for (w[e] = n, e = 0; e < n.length; e++) g.add(n[e]);
  }
  var L = !(typeof window > "u" || typeof window.document > "u" || typeof window.document.createElement > "u"), E = Object.prototype.hasOwnProperty, k = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, U = {}, B = {};
  function J(e) {
    return E.call(B, e) ? !0 : E.call(U, e) ? !1 : k.test(e) ? B[e] = !0 : (U[e] = !0, !1);
  }
  function ie(e, n, t, r) {
    if (t !== null && t.type === 0) return !1;
    switch (typeof n) {
      case "function":
      case "symbol":
        return !0;
      case "boolean":
        return r ? !1 : t !== null ? !t.acceptsBooleans : (e = e.toLowerCase().slice(0, 5), e !== "data-" && e !== "aria-");
      default:
        return !1;
    }
  }
  function ve(e, n, t, r) {
    if (n === null || typeof n > "u" || ie(e, n, t, r)) return !0;
    if (r) return !1;
    if (t !== null) switch (t.type) {
      case 3:
        return !n;
      case 4:
        return n === !1;
      case 5:
        return isNaN(n);
      case 6:
        return isNaN(n) || 1 > n;
    }
    return !1;
  }
  function K(e, n, t, r, l, i, s) {
    this.acceptsBooleans = n === 2 || n === 3 || n === 4, this.attributeName = r, this.attributeNamespace = l, this.mustUseProperty = t, this.propertyName = e, this.type = n, this.sanitizeURL = i, this.removeEmptyString = s;
  }
  var X = {};
  "children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e) {
    X[e] = new K(e, 0, !1, e, null, !1, !1);
  }), [["acceptCharset", "accept-charset"], ["className", "class"], ["htmlFor", "for"], ["httpEquiv", "http-equiv"]].forEach(function(e) {
    var n = e[0];
    X[n] = new K(n, 1, !1, e[1], null, !1, !1);
  }), ["contentEditable", "draggable", "spellCheck", "value"].forEach(function(e) {
    X[e] = new K(e, 2, !1, e.toLowerCase(), null, !1, !1);
  }), ["autoReverse", "externalResourcesRequired", "focusable", "preserveAlpha"].forEach(function(e) {
    X[e] = new K(e, 2, !1, e, null, !1, !1);
  }), "allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e) {
    X[e] = new K(e, 3, !1, e.toLowerCase(), null, !1, !1);
  }), ["checked", "multiple", "muted", "selected"].forEach(function(e) {
    X[e] = new K(e, 3, !0, e, null, !1, !1);
  }), ["capture", "download"].forEach(function(e) {
    X[e] = new K(e, 4, !1, e, null, !1, !1);
  }), ["cols", "rows", "size", "span"].forEach(function(e) {
    X[e] = new K(e, 6, !1, e, null, !1, !1);
  }), ["rowSpan", "start"].forEach(function(e) {
    X[e] = new K(e, 5, !1, e.toLowerCase(), null, !1, !1);
  });
  var b = /[\-:]([a-z])/g;
  function Ne(e) {
    return e[1].toUpperCase();
  }
  "accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e) {
    var n = e.replace(
      b,
      Ne
    );
    X[n] = new K(n, 1, !1, e, null, !1, !1);
  }), "xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e) {
    var n = e.replace(b, Ne);
    X[n] = new K(n, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
  }), ["xml:base", "xml:lang", "xml:space"].forEach(function(e) {
    var n = e.replace(b, Ne);
    X[n] = new K(n, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
  }), ["tabIndex", "crossOrigin"].forEach(function(e) {
    X[e] = new K(e, 1, !1, e.toLowerCase(), null, !1, !1);
  }), X.xlinkHref = new K("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1), ["src", "href", "action", "formAction"].forEach(function(e) {
    X[e] = new K(e, 1, !1, e.toLowerCase(), null, !0, !0);
  });
  function ge(e, n, t, r) {
    var l = X.hasOwnProperty(n) ? X[n] : null;
    (l !== null ? l.type !== 0 : r || !(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") && (ve(n, t, l, r) && (t = null), r || l === null ? J(n) && (t === null ? e.removeAttribute(n) : e.setAttribute(n, "" + t)) : l.mustUseProperty ? e[l.propertyName] = t === null ? l.type === 3 ? !1 : "" : t : (n = l.attributeName, r = l.attributeNamespace, t === null ? e.removeAttribute(n) : (l = l.type, t = l === 3 || l === 4 && t === !0 ? "" : "" + t, r ? e.setAttributeNS(r, n, t) : e.setAttribute(n, t))));
  }
  var fe = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, Te = Symbol.for("react.element"), ke = Symbol.for("react.portal"), pe = Symbol.for("react.fragment"), Q = Symbol.for("react.strict_mode"), Ze = Symbol.for("react.profiler"), We = Symbol.for("react.provider"), Je = Symbol.for("react.context"), ze = Symbol.for("react.forward_ref"), V = Symbol.for("react.suspense"), _ = Symbol.for("react.suspense_list"), Le = Symbol.for("react.memo"), Ce = Symbol.for("react.lazy"), ae = Symbol.for("react.offscreen"), O = Symbol.iterator;
  function T(e) {
    return e === null || typeof e != "object" ? null : (e = O && e[O] || e["@@iterator"], typeof e == "function" ? e : null);
  }
  var P = Object.assign, h;
  function S(e) {
    if (h === void 0) try {
      throw Error();
    } catch (t) {
      var n = t.stack.trim().match(/\n( *(at )?)/);
      h = n && n[1] || "";
    }
    return `
` + h + e;
  }
  var Z = !1;
  function Y(e, n) {
    if (!e || Z) return "";
    Z = !0;
    var t = Error.prepareStackTrace;
    Error.prepareStackTrace = void 0;
    try {
      if (n) if (n = function() {
        throw Error();
      }, Object.defineProperty(n.prototype, "props", { set: function() {
        throw Error();
      } }), typeof Reflect == "object" && Reflect.construct) {
        try {
          Reflect.construct(n, []);
        } catch (y) {
          var r = y;
        }
        Reflect.construct(e, [], n);
      } else {
        try {
          n.call();
        } catch (y) {
          r = y;
        }
        e.call(n.prototype);
      }
      else {
        try {
          throw Error();
        } catch (y) {
          r = y;
        }
        e();
      }
    } catch (y) {
      if (y && r && typeof y.stack == "string") {
        for (var l = y.stack.split(`
`), i = r.stack.split(`
`), s = l.length - 1, d = i.length - 1; 1 <= s && 0 <= d && l[s] !== i[d]; ) d--;
        for (; 1 <= s && 0 <= d; s--, d--) if (l[s] !== i[d]) {
          if (s !== 1 || d !== 1)
            do
              if (s--, d--, 0 > d || l[s] !== i[d]) {
                var f = `
` + l[s].replace(" at new ", " at ");
                return e.displayName && f.includes("<anonymous>") && (f = f.replace("<anonymous>", e.displayName)), f;
              }
            while (1 <= s && 0 <= d);
          break;
        }
      }
    } finally {
      Z = !1, Error.prepareStackTrace = t;
    }
    return (e = e ? e.displayName || e.name : "") ? S(e) : "";
  }
  function ee(e) {
    switch (e.tag) {
      case 5:
        return S(e.type);
      case 16:
        return S("Lazy");
      case 13:
        return S("Suspense");
      case 19:
        return S("SuspenseList");
      case 0:
      case 2:
      case 15:
        return e = Y(e.type, !1), e;
      case 11:
        return e = Y(e.type.render, !1), e;
      case 1:
        return e = Y(e.type, !0), e;
      default:
        return "";
    }
  }
  function ne(e) {
    if (e == null) return null;
    if (typeof e == "function") return e.displayName || e.name || null;
    if (typeof e == "string") return e;
    switch (e) {
      case pe:
        return "Fragment";
      case ke:
        return "Portal";
      case Ze:
        return "Profiler";
      case Q:
        return "StrictMode";
      case V:
        return "Suspense";
      case _:
        return "SuspenseList";
    }
    if (typeof e == "object") switch (e.$$typeof) {
      case Je:
        return (e.displayName || "Context") + ".Consumer";
      case We:
        return (e._context.displayName || "Context") + ".Provider";
      case ze:
        var n = e.render;
        return e = e.displayName, e || (e = n.displayName || n.name || "", e = e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef"), e;
      case Le:
        return n = e.displayName || null, n !== null ? n : ne(e.type) || "Memo";
      case Ce:
        n = e._payload, e = e._init;
        try {
          return ne(e(n));
        } catch {
        }
    }
    return null;
  }
  function oe(e) {
    var n = e.type;
    switch (e.tag) {
      case 24:
        return "Cache";
      case 9:
        return (n.displayName || "Context") + ".Consumer";
      case 10:
        return (n._context.displayName || "Context") + ".Provider";
      case 18:
        return "DehydratedFragment";
      case 11:
        return e = n.render, e = e.displayName || e.name || "", n.displayName || (e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef");
      case 7:
        return "Fragment";
      case 5:
        return n;
      case 4:
        return "Portal";
      case 3:
        return "Root";
      case 6:
        return "Text";
      case 16:
        return ne(n);
      case 8:
        return n === Q ? "StrictMode" : "Mode";
      case 22:
        return "Offscreen";
      case 12:
        return "Profiler";
      case 21:
        return "Scope";
      case 13:
        return "Suspense";
      case 19:
        return "SuspenseList";
      case 25:
        return "TracingMarker";
      case 1:
      case 0:
      case 17:
      case 2:
      case 14:
      case 15:
        if (typeof n == "function") return n.displayName || n.name || null;
        if (typeof n == "string") return n;
    }
    return null;
  }
  function re(e) {
    switch (typeof e) {
      case "boolean":
      case "number":
      case "string":
      case "undefined":
        return e;
      case "object":
        return e;
      default:
        return "";
    }
  }
  function he(e) {
    var n = e.type;
    return (e = e.nodeName) && e.toLowerCase() === "input" && (n === "checkbox" || n === "radio");
  }
  function tn(e) {
    var n = he(e) ? "checked" : "value", t = Object.getOwnPropertyDescriptor(e.constructor.prototype, n), r = "" + e[n];
    if (!e.hasOwnProperty(n) && typeof t < "u" && typeof t.get == "function" && typeof t.set == "function") {
      var l = t.get, i = t.set;
      return Object.defineProperty(e, n, { configurable: !0, get: function() {
        return l.call(this);
      }, set: function(s) {
        r = "" + s, i.call(this, s);
      } }), Object.defineProperty(e, n, { enumerable: t.enumerable }), { getValue: function() {
        return r;
      }, setValue: function(s) {
        r = "" + s;
      }, stopTracking: function() {
        e._valueTracker = null, delete e[n];
      } };
    }
  }
  function Pr(e) {
    e._valueTracker || (e._valueTracker = tn(e));
  }
  function Yo(e) {
    if (!e) return !1;
    var n = e._valueTracker;
    if (!n) return !0;
    var t = n.getValue(), r = "";
    return e && (r = he(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== t ? (n.setValue(e), !0) : !1;
  }
  function Tr(e) {
    if (e = e || (typeof document < "u" ? document : void 0), typeof e > "u") return null;
    try {
      return e.activeElement || e.body;
    } catch {
      return e.body;
    }
  }
  function Kl(e, n) {
    var t = n.checked;
    return P({}, n, { defaultChecked: void 0, defaultValue: void 0, value: void 0, checked: t ?? e._wrapperState.initialChecked });
  }
  function bo(e, n) {
    var t = n.defaultValue == null ? "" : n.defaultValue, r = n.checked != null ? n.checked : n.defaultChecked;
    t = re(n.value != null ? n.value : t), e._wrapperState = { initialChecked: r, initialValue: t, controlled: n.type === "checkbox" || n.type === "radio" ? n.checked != null : n.value != null };
  }
  function _o(e, n) {
    n = n.checked, n != null && ge(e, "checked", n, !1);
  }
  function Ql(e, n) {
    _o(e, n);
    var t = re(n.value), r = n.type;
    if (t != null) r === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + t) : e.value !== "" + t && (e.value = "" + t);
    else if (r === "submit" || r === "reset") {
      e.removeAttribute("value");
      return;
    }
    n.hasOwnProperty("value") ? Gl(e, n.type, t) : n.hasOwnProperty("defaultValue") && Gl(e, n.type, re(n.defaultValue)), n.checked == null && n.defaultChecked != null && (e.defaultChecked = !!n.defaultChecked);
  }
  function $o(e, n, t) {
    if (n.hasOwnProperty("value") || n.hasOwnProperty("defaultValue")) {
      var r = n.type;
      if (!(r !== "submit" && r !== "reset" || n.value !== void 0 && n.value !== null)) return;
      n = "" + e._wrapperState.initialValue, t || n === e.value || (e.value = n), e.defaultValue = n;
    }
    t = e.name, t !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, t !== "" && (e.name = t);
  }
  function Gl(e, n, t) {
    (n !== "number" || Tr(e.ownerDocument) !== e) && (t == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + t && (e.defaultValue = "" + t));
  }
  var Ut = Array.isArray;
  function ht(e, n, t, r) {
    if (e = e.options, n) {
      n = {};
      for (var l = 0; l < t.length; l++) n["$" + t[l]] = !0;
      for (t = 0; t < e.length; t++) l = n.hasOwnProperty("$" + e[t].value), e[t].selected !== l && (e[t].selected = l), l && r && (e[t].defaultSelected = !0);
    } else {
      for (t = "" + re(t), n = null, l = 0; l < e.length; l++) {
        if (e[l].value === t) {
          e[l].selected = !0, r && (e[l].defaultSelected = !0);
          return;
        }
        n !== null || e[l].disabled || (n = e[l]);
      }
      n !== null && (n.selected = !0);
    }
  }
  function Yl(e, n) {
    if (n.dangerouslySetInnerHTML != null) throw Error(c(91));
    return P({}, n, { value: void 0, defaultValue: void 0, children: "" + e._wrapperState.initialValue });
  }
  function es(e, n) {
    var t = n.value;
    if (t == null) {
      if (t = n.children, n = n.defaultValue, t != null) {
        if (n != null) throw Error(c(92));
        if (Ut(t)) {
          if (1 < t.length) throw Error(c(93));
          t = t[0];
        }
        n = t;
      }
      n == null && (n = ""), t = n;
    }
    e._wrapperState = { initialValue: re(t) };
  }
  function ns(e, n) {
    var t = re(n.value), r = re(n.defaultValue);
    t != null && (t = "" + t, t !== e.value && (e.value = t), n.defaultValue == null && e.defaultValue !== t && (e.defaultValue = t)), r != null && (e.defaultValue = "" + r);
  }
  function ts(e) {
    var n = e.textContent;
    n === e._wrapperState.initialValue && n !== "" && n !== null && (e.value = n);
  }
  function rs(e) {
    switch (e) {
      case "svg":
        return "http://www.w3.org/2000/svg";
      case "math":
        return "http://www.w3.org/1998/Math/MathML";
      default:
        return "http://www.w3.org/1999/xhtml";
    }
  }
  function bl(e, n) {
    return e == null || e === "http://www.w3.org/1999/xhtml" ? rs(n) : e === "http://www.w3.org/2000/svg" && n === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
  }
  var Lr, ls = (function(e) {
    return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(n, t, r, l) {
      MSApp.execUnsafeLocalFunction(function() {
        return e(n, t, r, l);
      });
    } : e;
  })(function(e, n) {
    if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = n;
    else {
      for (Lr = Lr || document.createElement("div"), Lr.innerHTML = "<svg>" + n.valueOf().toString() + "</svg>", n = Lr.firstChild; e.firstChild; ) e.removeChild(e.firstChild);
      for (; n.firstChild; ) e.appendChild(n.firstChild);
    }
  });
  function qt(e, n) {
    if (n) {
      var t = e.firstChild;
      if (t && t === e.lastChild && t.nodeType === 3) {
        t.nodeValue = n;
        return;
      }
    }
    e.textContent = n;
  }
  var Ht = {
    animationIterationCount: !0,
    aspectRatio: !0,
    borderImageOutset: !0,
    borderImageSlice: !0,
    borderImageWidth: !0,
    boxFlex: !0,
    boxFlexGroup: !0,
    boxOrdinalGroup: !0,
    columnCount: !0,
    columns: !0,
    flex: !0,
    flexGrow: !0,
    flexPositive: !0,
    flexShrink: !0,
    flexNegative: !0,
    flexOrder: !0,
    gridArea: !0,
    gridRow: !0,
    gridRowEnd: !0,
    gridRowSpan: !0,
    gridRowStart: !0,
    gridColumn: !0,
    gridColumnEnd: !0,
    gridColumnSpan: !0,
    gridColumnStart: !0,
    fontWeight: !0,
    lineClamp: !0,
    lineHeight: !0,
    opacity: !0,
    order: !0,
    orphans: !0,
    tabSize: !0,
    widows: !0,
    zIndex: !0,
    zoom: !0,
    fillOpacity: !0,
    floodOpacity: !0,
    stopOpacity: !0,
    strokeDasharray: !0,
    strokeDashoffset: !0,
    strokeMiterlimit: !0,
    strokeOpacity: !0,
    strokeWidth: !0
  }, hc = ["Webkit", "ms", "Moz", "O"];
  Object.keys(Ht).forEach(function(e) {
    hc.forEach(function(n) {
      n = n + e.charAt(0).toUpperCase() + e.substring(1), Ht[n] = Ht[e];
    });
  });
  function is(e, n, t) {
    return n == null || typeof n == "boolean" || n === "" ? "" : t || typeof n != "number" || n === 0 || Ht.hasOwnProperty(e) && Ht[e] ? ("" + n).trim() : n + "px";
  }
  function os(e, n) {
    e = e.style;
    for (var t in n) if (n.hasOwnProperty(t)) {
      var r = t.indexOf("--") === 0, l = is(t, n[t], r);
      t === "float" && (t = "cssFloat"), r ? e.setProperty(t, l) : e[t] = l;
    }
  }
  var mc = P({ menuitem: !0 }, { area: !0, base: !0, br: !0, col: !0, embed: !0, hr: !0, img: !0, input: !0, keygen: !0, link: !0, meta: !0, param: !0, source: !0, track: !0, wbr: !0 });
  function _l(e, n) {
    if (n) {
      if (mc[e] && (n.children != null || n.dangerouslySetInnerHTML != null)) throw Error(c(137, e));
      if (n.dangerouslySetInnerHTML != null) {
        if (n.children != null) throw Error(c(60));
        if (typeof n.dangerouslySetInnerHTML != "object" || !("__html" in n.dangerouslySetInnerHTML)) throw Error(c(61));
      }
      if (n.style != null && typeof n.style != "object") throw Error(c(62));
    }
  }
  function $l(e, n) {
    if (e.indexOf("-") === -1) return typeof n.is == "string";
    switch (e) {
      case "annotation-xml":
      case "color-profile":
      case "font-face":
      case "font-face-src":
      case "font-face-uri":
      case "font-face-format":
      case "font-face-name":
      case "missing-glyph":
        return !1;
      default:
        return !0;
    }
  }
  var ei = null;
  function ni(e) {
    return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
  }
  var ti = null, mt = null, vt = null;
  function ss(e) {
    if (e = ar(e)) {
      if (typeof ti != "function") throw Error(c(280));
      var n = e.stateNode;
      n && (n = el(n), ti(e.stateNode, e.type, n));
    }
  }
  function us(e) {
    mt ? vt ? vt.push(e) : vt = [e] : mt = e;
  }
  function as() {
    if (mt) {
      var e = mt, n = vt;
      if (vt = mt = null, ss(e), n) for (e = 0; e < n.length; e++) ss(n[e]);
    }
  }
  function cs(e, n) {
    return e(n);
  }
  function ds() {
  }
  var ri = !1;
  function fs(e, n, t) {
    if (ri) return e(n, t);
    ri = !0;
    try {
      return cs(e, n, t);
    } finally {
      ri = !1, (mt !== null || vt !== null) && (ds(), as());
    }
  }
  function At(e, n) {
    var t = e.stateNode;
    if (t === null) return null;
    var r = el(t);
    if (r === null) return null;
    t = r[n];
    e: switch (n) {
      case "onClick":
      case "onClickCapture":
      case "onDoubleClick":
      case "onDoubleClickCapture":
      case "onMouseDown":
      case "onMouseDownCapture":
      case "onMouseMove":
      case "onMouseMoveCapture":
      case "onMouseUp":
      case "onMouseUpCapture":
      case "onMouseEnter":
        (r = !r.disabled) || (e = e.type, r = !(e === "button" || e === "input" || e === "select" || e === "textarea")), e = !r;
        break e;
      default:
        e = !1;
    }
    if (e) return null;
    if (t && typeof t != "function") throw Error(c(231, n, typeof t));
    return t;
  }
  var li = !1;
  if (L) try {
    var Bt = {};
    Object.defineProperty(Bt, "passive", { get: function() {
      li = !0;
    } }), window.addEventListener("test", Bt, Bt), window.removeEventListener("test", Bt, Bt);
  } catch {
    li = !1;
  }
  function vc(e, n, t, r, l, i, s, d, f) {
    var y = Array.prototype.slice.call(arguments, 3);
    try {
      n.apply(t, y);
    } catch (N) {
      this.onError(N);
    }
  }
  var Xt = !1, Or = null, Fr = !1, ii = null, gc = { onError: function(e) {
    Xt = !0, Or = e;
  } };
  function yc(e, n, t, r, l, i, s, d, f) {
    Xt = !1, Or = null, vc.apply(gc, arguments);
  }
  function xc(e, n, t, r, l, i, s, d, f) {
    if (yc.apply(this, arguments), Xt) {
      if (Xt) {
        var y = Or;
        Xt = !1, Or = null;
      } else throw Error(c(198));
      Fr || (Fr = !0, ii = y);
    }
  }
  function nt(e) {
    var n = e, t = e;
    if (e.alternate) for (; n.return; ) n = n.return;
    else {
      e = n;
      do
        n = e, (n.flags & 4098) !== 0 && (t = n.return), e = n.return;
      while (e);
    }
    return n.tag === 3 ? t : null;
  }
  function ps(e) {
    if (e.tag === 13) {
      var n = e.memoizedState;
      if (n === null && (e = e.alternate, e !== null && (n = e.memoizedState)), n !== null) return n.dehydrated;
    }
    return null;
  }
  function hs(e) {
    if (nt(e) !== e) throw Error(c(188));
  }
  function wc(e) {
    var n = e.alternate;
    if (!n) {
      if (n = nt(e), n === null) throw Error(c(188));
      return n !== e ? null : e;
    }
    for (var t = e, r = n; ; ) {
      var l = t.return;
      if (l === null) break;
      var i = l.alternate;
      if (i === null) {
        if (r = l.return, r !== null) {
          t = r;
          continue;
        }
        break;
      }
      if (l.child === i.child) {
        for (i = l.child; i; ) {
          if (i === t) return hs(l), e;
          if (i === r) return hs(l), n;
          i = i.sibling;
        }
        throw Error(c(188));
      }
      if (t.return !== r.return) t = l, r = i;
      else {
        for (var s = !1, d = l.child; d; ) {
          if (d === t) {
            s = !0, t = l, r = i;
            break;
          }
          if (d === r) {
            s = !0, r = l, t = i;
            break;
          }
          d = d.sibling;
        }
        if (!s) {
          for (d = i.child; d; ) {
            if (d === t) {
              s = !0, t = i, r = l;
              break;
            }
            if (d === r) {
              s = !0, r = i, t = l;
              break;
            }
            d = d.sibling;
          }
          if (!s) throw Error(c(189));
        }
      }
      if (t.alternate !== r) throw Error(c(190));
    }
    if (t.tag !== 3) throw Error(c(188));
    return t.stateNode.current === t ? e : n;
  }
  function ms(e) {
    return e = wc(e), e !== null ? vs(e) : null;
  }
  function vs(e) {
    if (e.tag === 5 || e.tag === 6) return e;
    for (e = e.child; e !== null; ) {
      var n = vs(e);
      if (n !== null) return n;
      e = e.sibling;
    }
    return null;
  }
  var gs = a.unstable_scheduleCallback, ys = a.unstable_cancelCallback, kc = a.unstable_shouldYield, Sc = a.unstable_requestPaint, Se = a.unstable_now, jc = a.unstable_getCurrentPriorityLevel, oi = a.unstable_ImmediatePriority, xs = a.unstable_UserBlockingPriority, Mr = a.unstable_NormalPriority, Nc = a.unstable_LowPriority, ws = a.unstable_IdlePriority, Ir = null, Sn = null;
  function Cc(e) {
    if (Sn && typeof Sn.onCommitFiberRoot == "function") try {
      Sn.onCommitFiberRoot(Ir, e, void 0, (e.current.flags & 128) === 128);
    } catch {
    }
  }
  var hn = Math.clz32 ? Math.clz32 : Rc, Ec = Math.log, zc = Math.LN2;
  function Rc(e) {
    return e >>>= 0, e === 0 ? 32 : 31 - (Ec(e) / zc | 0) | 0;
  }
  var Wr = 64, Dr = 4194304;
  function Zt(e) {
    switch (e & -e) {
      case 1:
        return 1;
      case 2:
        return 2;
      case 4:
        return 4;
      case 8:
        return 8;
      case 16:
        return 16;
      case 32:
        return 32;
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return e & 4194240;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return e & 130023424;
      case 134217728:
        return 134217728;
      case 268435456:
        return 268435456;
      case 536870912:
        return 536870912;
      case 1073741824:
        return 1073741824;
      default:
        return e;
    }
  }
  function Vr(e, n) {
    var t = e.pendingLanes;
    if (t === 0) return 0;
    var r = 0, l = e.suspendedLanes, i = e.pingedLanes, s = t & 268435455;
    if (s !== 0) {
      var d = s & ~l;
      d !== 0 ? r = Zt(d) : (i &= s, i !== 0 && (r = Zt(i)));
    } else s = t & ~l, s !== 0 ? r = Zt(s) : i !== 0 && (r = Zt(i));
    if (r === 0) return 0;
    if (n !== 0 && n !== r && (n & l) === 0 && (l = r & -r, i = n & -n, l >= i || l === 16 && (i & 4194240) !== 0)) return n;
    if ((r & 4) !== 0 && (r |= t & 16), n = e.entangledLanes, n !== 0) for (e = e.entanglements, n &= r; 0 < n; ) t = 31 - hn(n), l = 1 << t, r |= e[t], n &= ~l;
    return r;
  }
  function Pc(e, n) {
    switch (e) {
      case 1:
      case 2:
      case 4:
        return n + 250;
      case 8:
      case 16:
      case 32:
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return n + 5e3;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return -1;
      case 134217728:
      case 268435456:
      case 536870912:
      case 1073741824:
        return -1;
      default:
        return -1;
    }
  }
  function Tc(e, n) {
    for (var t = e.suspendedLanes, r = e.pingedLanes, l = e.expirationTimes, i = e.pendingLanes; 0 < i; ) {
      var s = 31 - hn(i), d = 1 << s, f = l[s];
      f === -1 ? ((d & t) === 0 || (d & r) !== 0) && (l[s] = Pc(d, n)) : f <= n && (e.expiredLanes |= d), i &= ~d;
    }
  }
  function si(e) {
    return e = e.pendingLanes & -1073741825, e !== 0 ? e : e & 1073741824 ? 1073741824 : 0;
  }
  function ks() {
    var e = Wr;
    return Wr <<= 1, (Wr & 4194240) === 0 && (Wr = 64), e;
  }
  function ui(e) {
    for (var n = [], t = 0; 31 > t; t++) n.push(e);
    return n;
  }
  function Jt(e, n, t) {
    e.pendingLanes |= n, n !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, n = 31 - hn(n), e[n] = t;
  }
  function Lc(e, n) {
    var t = e.pendingLanes & ~n;
    e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= n, e.mutableReadLanes &= n, e.entangledLanes &= n, n = e.entanglements;
    var r = e.eventTimes;
    for (e = e.expirationTimes; 0 < t; ) {
      var l = 31 - hn(t), i = 1 << l;
      n[l] = 0, r[l] = -1, e[l] = -1, t &= ~i;
    }
  }
  function ai(e, n) {
    var t = e.entangledLanes |= n;
    for (e = e.entanglements; t; ) {
      var r = 31 - hn(t), l = 1 << r;
      l & n | e[r] & n && (e[r] |= n), t &= ~l;
    }
  }
  var le = 0;
  function Ss(e) {
    return e &= -e, 1 < e ? 4 < e ? (e & 268435455) !== 0 ? 16 : 536870912 : 4 : 1;
  }
  var js, ci, Ns, Cs, Es, di = !1, Ur = [], Wn = null, Dn = null, Vn = null, Kt = /* @__PURE__ */ new Map(), Qt = /* @__PURE__ */ new Map(), Un = [], Oc = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
  function zs(e, n) {
    switch (e) {
      case "focusin":
      case "focusout":
        Wn = null;
        break;
      case "dragenter":
      case "dragleave":
        Dn = null;
        break;
      case "mouseover":
      case "mouseout":
        Vn = null;
        break;
      case "pointerover":
      case "pointerout":
        Kt.delete(n.pointerId);
        break;
      case "gotpointercapture":
      case "lostpointercapture":
        Qt.delete(n.pointerId);
    }
  }
  function Gt(e, n, t, r, l, i) {
    return e === null || e.nativeEvent !== i ? (e = { blockedOn: n, domEventName: t, eventSystemFlags: r, nativeEvent: i, targetContainers: [l] }, n !== null && (n = ar(n), n !== null && ci(n)), e) : (e.eventSystemFlags |= r, n = e.targetContainers, l !== null && n.indexOf(l) === -1 && n.push(l), e);
  }
  function Fc(e, n, t, r, l) {
    switch (n) {
      case "focusin":
        return Wn = Gt(Wn, e, n, t, r, l), !0;
      case "dragenter":
        return Dn = Gt(Dn, e, n, t, r, l), !0;
      case "mouseover":
        return Vn = Gt(Vn, e, n, t, r, l), !0;
      case "pointerover":
        var i = l.pointerId;
        return Kt.set(i, Gt(Kt.get(i) || null, e, n, t, r, l)), !0;
      case "gotpointercapture":
        return i = l.pointerId, Qt.set(i, Gt(Qt.get(i) || null, e, n, t, r, l)), !0;
    }
    return !1;
  }
  function Rs(e) {
    var n = tt(e.target);
    if (n !== null) {
      var t = nt(n);
      if (t !== null) {
        if (n = t.tag, n === 13) {
          if (n = ps(t), n !== null) {
            e.blockedOn = n, Es(e.priority, function() {
              Ns(t);
            });
            return;
          }
        } else if (n === 3 && t.stateNode.current.memoizedState.isDehydrated) {
          e.blockedOn = t.tag === 3 ? t.stateNode.containerInfo : null;
          return;
        }
      }
    }
    e.blockedOn = null;
  }
  function qr(e) {
    if (e.blockedOn !== null) return !1;
    for (var n = e.targetContainers; 0 < n.length; ) {
      var t = pi(e.domEventName, e.eventSystemFlags, n[0], e.nativeEvent);
      if (t === null) {
        t = e.nativeEvent;
        var r = new t.constructor(t.type, t);
        ei = r, t.target.dispatchEvent(r), ei = null;
      } else return n = ar(t), n !== null && ci(n), e.blockedOn = t, !1;
      n.shift();
    }
    return !0;
  }
  function Ps(e, n, t) {
    qr(e) && t.delete(n);
  }
  function Mc() {
    di = !1, Wn !== null && qr(Wn) && (Wn = null), Dn !== null && qr(Dn) && (Dn = null), Vn !== null && qr(Vn) && (Vn = null), Kt.forEach(Ps), Qt.forEach(Ps);
  }
  function Yt(e, n) {
    e.blockedOn === n && (e.blockedOn = null, di || (di = !0, a.unstable_scheduleCallback(a.unstable_NormalPriority, Mc)));
  }
  function bt(e) {
    function n(l) {
      return Yt(l, e);
    }
    if (0 < Ur.length) {
      Yt(Ur[0], e);
      for (var t = 1; t < Ur.length; t++) {
        var r = Ur[t];
        r.blockedOn === e && (r.blockedOn = null);
      }
    }
    for (Wn !== null && Yt(Wn, e), Dn !== null && Yt(Dn, e), Vn !== null && Yt(Vn, e), Kt.forEach(n), Qt.forEach(n), t = 0; t < Un.length; t++) r = Un[t], r.blockedOn === e && (r.blockedOn = null);
    for (; 0 < Un.length && (t = Un[0], t.blockedOn === null); ) Rs(t), t.blockedOn === null && Un.shift();
  }
  var gt = fe.ReactCurrentBatchConfig, Hr = !0;
  function Ic(e, n, t, r) {
    var l = le, i = gt.transition;
    gt.transition = null;
    try {
      le = 1, fi(e, n, t, r);
    } finally {
      le = l, gt.transition = i;
    }
  }
  function Wc(e, n, t, r) {
    var l = le, i = gt.transition;
    gt.transition = null;
    try {
      le = 4, fi(e, n, t, r);
    } finally {
      le = l, gt.transition = i;
    }
  }
  function fi(e, n, t, r) {
    if (Hr) {
      var l = pi(e, n, t, r);
      if (l === null) Ti(e, n, r, Ar, t), zs(e, r);
      else if (Fc(l, e, n, t, r)) r.stopPropagation();
      else if (zs(e, r), n & 4 && -1 < Oc.indexOf(e)) {
        for (; l !== null; ) {
          var i = ar(l);
          if (i !== null && js(i), i = pi(e, n, t, r), i === null && Ti(e, n, r, Ar, t), i === l) break;
          l = i;
        }
        l !== null && r.stopPropagation();
      } else Ti(e, n, r, null, t);
    }
  }
  var Ar = null;
  function pi(e, n, t, r) {
    if (Ar = null, e = ni(r), e = tt(e), e !== null) if (n = nt(e), n === null) e = null;
    else if (t = n.tag, t === 13) {
      if (e = ps(n), e !== null) return e;
      e = null;
    } else if (t === 3) {
      if (n.stateNode.current.memoizedState.isDehydrated) return n.tag === 3 ? n.stateNode.containerInfo : null;
      e = null;
    } else n !== e && (e = null);
    return Ar = e, null;
  }
  function Ts(e) {
    switch (e) {
      case "cancel":
      case "click":
      case "close":
      case "contextmenu":
      case "copy":
      case "cut":
      case "auxclick":
      case "dblclick":
      case "dragend":
      case "dragstart":
      case "drop":
      case "focusin":
      case "focusout":
      case "input":
      case "invalid":
      case "keydown":
      case "keypress":
      case "keyup":
      case "mousedown":
      case "mouseup":
      case "paste":
      case "pause":
      case "play":
      case "pointercancel":
      case "pointerdown":
      case "pointerup":
      case "ratechange":
      case "reset":
      case "resize":
      case "seeked":
      case "submit":
      case "touchcancel":
      case "touchend":
      case "touchstart":
      case "volumechange":
      case "change":
      case "selectionchange":
      case "textInput":
      case "compositionstart":
      case "compositionend":
      case "compositionupdate":
      case "beforeblur":
      case "afterblur":
      case "beforeinput":
      case "blur":
      case "fullscreenchange":
      case "focus":
      case "hashchange":
      case "popstate":
      case "select":
      case "selectstart":
        return 1;
      case "drag":
      case "dragenter":
      case "dragexit":
      case "dragleave":
      case "dragover":
      case "mousemove":
      case "mouseout":
      case "mouseover":
      case "pointermove":
      case "pointerout":
      case "pointerover":
      case "scroll":
      case "toggle":
      case "touchmove":
      case "wheel":
      case "mouseenter":
      case "mouseleave":
      case "pointerenter":
      case "pointerleave":
        return 4;
      case "message":
        switch (jc()) {
          case oi:
            return 1;
          case xs:
            return 4;
          case Mr:
          case Nc:
            return 16;
          case ws:
            return 536870912;
          default:
            return 16;
        }
      default:
        return 16;
    }
  }
  var qn = null, hi = null, Br = null;
  function Ls() {
    if (Br) return Br;
    var e, n = hi, t = n.length, r, l = "value" in qn ? qn.value : qn.textContent, i = l.length;
    for (e = 0; e < t && n[e] === l[e]; e++) ;
    var s = t - e;
    for (r = 1; r <= s && n[t - r] === l[i - r]; r++) ;
    return Br = l.slice(e, 1 < r ? 1 - r : void 0);
  }
  function Xr(e) {
    var n = e.keyCode;
    return "charCode" in e ? (e = e.charCode, e === 0 && n === 13 && (e = 13)) : e = n, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
  }
  function Zr() {
    return !0;
  }
  function Os() {
    return !1;
  }
  function rn(e) {
    function n(t, r, l, i, s) {
      this._reactName = t, this._targetInst = l, this.type = r, this.nativeEvent = i, this.target = s, this.currentTarget = null;
      for (var d in e) e.hasOwnProperty(d) && (t = e[d], this[d] = t ? t(i) : i[d]);
      return this.isDefaultPrevented = (i.defaultPrevented != null ? i.defaultPrevented : i.returnValue === !1) ? Zr : Os, this.isPropagationStopped = Os, this;
    }
    return P(n.prototype, { preventDefault: function() {
      this.defaultPrevented = !0;
      var t = this.nativeEvent;
      t && (t.preventDefault ? t.preventDefault() : typeof t.returnValue != "unknown" && (t.returnValue = !1), this.isDefaultPrevented = Zr);
    }, stopPropagation: function() {
      var t = this.nativeEvent;
      t && (t.stopPropagation ? t.stopPropagation() : typeof t.cancelBubble != "unknown" && (t.cancelBubble = !0), this.isPropagationStopped = Zr);
    }, persist: function() {
    }, isPersistent: Zr }), n;
  }
  var yt = { eventPhase: 0, bubbles: 0, cancelable: 0, timeStamp: function(e) {
    return e.timeStamp || Date.now();
  }, defaultPrevented: 0, isTrusted: 0 }, mi = rn(yt), _t = P({}, yt, { view: 0, detail: 0 }), Dc = rn(_t), vi, gi, $t, Jr = P({}, _t, { screenX: 0, screenY: 0, clientX: 0, clientY: 0, pageX: 0, pageY: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, getModifierState: xi, button: 0, buttons: 0, relatedTarget: function(e) {
    return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
  }, movementX: function(e) {
    return "movementX" in e ? e.movementX : (e !== $t && ($t && e.type === "mousemove" ? (vi = e.screenX - $t.screenX, gi = e.screenY - $t.screenY) : gi = vi = 0, $t = e), vi);
  }, movementY: function(e) {
    return "movementY" in e ? e.movementY : gi;
  } }), Fs = rn(Jr), Vc = P({}, Jr, { dataTransfer: 0 }), Uc = rn(Vc), qc = P({}, _t, { relatedTarget: 0 }), yi = rn(qc), Hc = P({}, yt, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }), Ac = rn(Hc), Bc = P({}, yt, { clipboardData: function(e) {
    return "clipboardData" in e ? e.clipboardData : window.clipboardData;
  } }), Xc = rn(Bc), Zc = P({}, yt, { data: 0 }), Ms = rn(Zc), Jc = {
    Esc: "Escape",
    Spacebar: " ",
    Left: "ArrowLeft",
    Up: "ArrowUp",
    Right: "ArrowRight",
    Down: "ArrowDown",
    Del: "Delete",
    Win: "OS",
    Menu: "ContextMenu",
    Apps: "ContextMenu",
    Scroll: "ScrollLock",
    MozPrintableKey: "Unidentified"
  }, Kc = {
    8: "Backspace",
    9: "Tab",
    12: "Clear",
    13: "Enter",
    16: "Shift",
    17: "Control",
    18: "Alt",
    19: "Pause",
    20: "CapsLock",
    27: "Escape",
    32: " ",
    33: "PageUp",
    34: "PageDown",
    35: "End",
    36: "Home",
    37: "ArrowLeft",
    38: "ArrowUp",
    39: "ArrowRight",
    40: "ArrowDown",
    45: "Insert",
    46: "Delete",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    144: "NumLock",
    145: "ScrollLock",
    224: "Meta"
  }, Qc = { Alt: "altKey", Control: "ctrlKey", Meta: "metaKey", Shift: "shiftKey" };
  function Gc(e) {
    var n = this.nativeEvent;
    return n.getModifierState ? n.getModifierState(e) : (e = Qc[e]) ? !!n[e] : !1;
  }
  function xi() {
    return Gc;
  }
  var Yc = P({}, _t, { key: function(e) {
    if (e.key) {
      var n = Jc[e.key] || e.key;
      if (n !== "Unidentified") return n;
    }
    return e.type === "keypress" ? (e = Xr(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Kc[e.keyCode] || "Unidentified" : "";
  }, code: 0, location: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, repeat: 0, locale: 0, getModifierState: xi, charCode: function(e) {
    return e.type === "keypress" ? Xr(e) : 0;
  }, keyCode: function(e) {
    return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  }, which: function(e) {
    return e.type === "keypress" ? Xr(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  } }), bc = rn(Yc), _c = P({}, Jr, { pointerId: 0, width: 0, height: 0, pressure: 0, tangentialPressure: 0, tiltX: 0, tiltY: 0, twist: 0, pointerType: 0, isPrimary: 0 }), Is = rn(_c), $c = P({}, _t, { touches: 0, targetTouches: 0, changedTouches: 0, altKey: 0, metaKey: 0, ctrlKey: 0, shiftKey: 0, getModifierState: xi }), ed = rn($c), nd = P({}, yt, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }), td = rn(nd), rd = P({}, Jr, {
    deltaX: function(e) {
      return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
    },
    deltaY: function(e) {
      return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
    },
    deltaZ: 0,
    deltaMode: 0
  }), ld = rn(rd), id = [9, 13, 27, 32], wi = L && "CompositionEvent" in window, er = null;
  L && "documentMode" in document && (er = document.documentMode);
  var od = L && "TextEvent" in window && !er, Ws = L && (!wi || er && 8 < er && 11 >= er), Ds = " ", Vs = !1;
  function Us(e, n) {
    switch (e) {
      case "keyup":
        return id.indexOf(n.keyCode) !== -1;
      case "keydown":
        return n.keyCode !== 229;
      case "keypress":
      case "mousedown":
      case "focusout":
        return !0;
      default:
        return !1;
    }
  }
  function qs(e) {
    return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
  }
  var xt = !1;
  function sd(e, n) {
    switch (e) {
      case "compositionend":
        return qs(n);
      case "keypress":
        return n.which !== 32 ? null : (Vs = !0, Ds);
      case "textInput":
        return e = n.data, e === Ds && Vs ? null : e;
      default:
        return null;
    }
  }
  function ud(e, n) {
    if (xt) return e === "compositionend" || !wi && Us(e, n) ? (e = Ls(), Br = hi = qn = null, xt = !1, e) : null;
    switch (e) {
      case "paste":
        return null;
      case "keypress":
        if (!(n.ctrlKey || n.altKey || n.metaKey) || n.ctrlKey && n.altKey) {
          if (n.char && 1 < n.char.length) return n.char;
          if (n.which) return String.fromCharCode(n.which);
        }
        return null;
      case "compositionend":
        return Ws && n.locale !== "ko" ? null : n.data;
      default:
        return null;
    }
  }
  var ad = { color: !0, date: !0, datetime: !0, "datetime-local": !0, email: !0, month: !0, number: !0, password: !0, range: !0, search: !0, tel: !0, text: !0, time: !0, url: !0, week: !0 };
  function Hs(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n === "input" ? !!ad[e.type] : n === "textarea";
  }
  function As(e, n, t, r) {
    us(r), n = br(n, "onChange"), 0 < n.length && (t = new mi("onChange", "change", null, t, r), e.push({ event: t, listeners: n }));
  }
  var nr = null, tr = null;
  function cd(e) {
    ou(e, 0);
  }
  function Kr(e) {
    var n = Nt(e);
    if (Yo(n)) return e;
  }
  function dd(e, n) {
    if (e === "change") return n;
  }
  var Bs = !1;
  if (L) {
    var ki;
    if (L) {
      var Si = "oninput" in document;
      if (!Si) {
        var Xs = document.createElement("div");
        Xs.setAttribute("oninput", "return;"), Si = typeof Xs.oninput == "function";
      }
      ki = Si;
    } else ki = !1;
    Bs = ki && (!document.documentMode || 9 < document.documentMode);
  }
  function Zs() {
    nr && (nr.detachEvent("onpropertychange", Js), tr = nr = null);
  }
  function Js(e) {
    if (e.propertyName === "value" && Kr(tr)) {
      var n = [];
      As(n, tr, e, ni(e)), fs(cd, n);
    }
  }
  function fd(e, n, t) {
    e === "focusin" ? (Zs(), nr = n, tr = t, nr.attachEvent("onpropertychange", Js)) : e === "focusout" && Zs();
  }
  function pd(e) {
    if (e === "selectionchange" || e === "keyup" || e === "keydown") return Kr(tr);
  }
  function hd(e, n) {
    if (e === "click") return Kr(n);
  }
  function md(e, n) {
    if (e === "input" || e === "change") return Kr(n);
  }
  function vd(e, n) {
    return e === n && (e !== 0 || 1 / e === 1 / n) || e !== e && n !== n;
  }
  var mn = typeof Object.is == "function" ? Object.is : vd;
  function rr(e, n) {
    if (mn(e, n)) return !0;
    if (typeof e != "object" || e === null || typeof n != "object" || n === null) return !1;
    var t = Object.keys(e), r = Object.keys(n);
    if (t.length !== r.length) return !1;
    for (r = 0; r < t.length; r++) {
      var l = t[r];
      if (!E.call(n, l) || !mn(e[l], n[l])) return !1;
    }
    return !0;
  }
  function Ks(e) {
    for (; e && e.firstChild; ) e = e.firstChild;
    return e;
  }
  function Qs(e, n) {
    var t = Ks(e);
    e = 0;
    for (var r; t; ) {
      if (t.nodeType === 3) {
        if (r = e + t.textContent.length, e <= n && r >= n) return { node: t, offset: n - e };
        e = r;
      }
      e: {
        for (; t; ) {
          if (t.nextSibling) {
            t = t.nextSibling;
            break e;
          }
          t = t.parentNode;
        }
        t = void 0;
      }
      t = Ks(t);
    }
  }
  function Gs(e, n) {
    return e && n ? e === n ? !0 : e && e.nodeType === 3 ? !1 : n && n.nodeType === 3 ? Gs(e, n.parentNode) : "contains" in e ? e.contains(n) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(n) & 16) : !1 : !1;
  }
  function Ys() {
    for (var e = window, n = Tr(); n instanceof e.HTMLIFrameElement; ) {
      try {
        var t = typeof n.contentWindow.location.href == "string";
      } catch {
        t = !1;
      }
      if (t) e = n.contentWindow;
      else break;
      n = Tr(e.document);
    }
    return n;
  }
  function ji(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n && (n === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || n === "textarea" || e.contentEditable === "true");
  }
  function gd(e) {
    var n = Ys(), t = e.focusedElem, r = e.selectionRange;
    if (n !== t && t && t.ownerDocument && Gs(t.ownerDocument.documentElement, t)) {
      if (r !== null && ji(t)) {
        if (n = r.start, e = r.end, e === void 0 && (e = n), "selectionStart" in t) t.selectionStart = n, t.selectionEnd = Math.min(e, t.value.length);
        else if (e = (n = t.ownerDocument || document) && n.defaultView || window, e.getSelection) {
          e = e.getSelection();
          var l = t.textContent.length, i = Math.min(r.start, l);
          r = r.end === void 0 ? i : Math.min(r.end, l), !e.extend && i > r && (l = r, r = i, i = l), l = Qs(t, i);
          var s = Qs(
            t,
            r
          );
          l && s && (e.rangeCount !== 1 || e.anchorNode !== l.node || e.anchorOffset !== l.offset || e.focusNode !== s.node || e.focusOffset !== s.offset) && (n = n.createRange(), n.setStart(l.node, l.offset), e.removeAllRanges(), i > r ? (e.addRange(n), e.extend(s.node, s.offset)) : (n.setEnd(s.node, s.offset), e.addRange(n)));
        }
      }
      for (n = [], e = t; e = e.parentNode; ) e.nodeType === 1 && n.push({ element: e, left: e.scrollLeft, top: e.scrollTop });
      for (typeof t.focus == "function" && t.focus(), t = 0; t < n.length; t++) e = n[t], e.element.scrollLeft = e.left, e.element.scrollTop = e.top;
    }
  }
  var yd = L && "documentMode" in document && 11 >= document.documentMode, wt = null, Ni = null, lr = null, Ci = !1;
  function bs(e, n, t) {
    var r = t.window === t ? t.document : t.nodeType === 9 ? t : t.ownerDocument;
    Ci || wt == null || wt !== Tr(r) || (r = wt, "selectionStart" in r && ji(r) ? r = { start: r.selectionStart, end: r.selectionEnd } : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = { anchorNode: r.anchorNode, anchorOffset: r.anchorOffset, focusNode: r.focusNode, focusOffset: r.focusOffset }), lr && rr(lr, r) || (lr = r, r = br(Ni, "onSelect"), 0 < r.length && (n = new mi("onSelect", "select", null, n, t), e.push({ event: n, listeners: r }), n.target = wt)));
  }
  function Qr(e, n) {
    var t = {};
    return t[e.toLowerCase()] = n.toLowerCase(), t["Webkit" + e] = "webkit" + n, t["Moz" + e] = "moz" + n, t;
  }
  var kt = { animationend: Qr("Animation", "AnimationEnd"), animationiteration: Qr("Animation", "AnimationIteration"), animationstart: Qr("Animation", "AnimationStart"), transitionend: Qr("Transition", "TransitionEnd") }, Ei = {}, _s = {};
  L && (_s = document.createElement("div").style, "AnimationEvent" in window || (delete kt.animationend.animation, delete kt.animationiteration.animation, delete kt.animationstart.animation), "TransitionEvent" in window || delete kt.transitionend.transition);
  function Gr(e) {
    if (Ei[e]) return Ei[e];
    if (!kt[e]) return e;
    var n = kt[e], t;
    for (t in n) if (n.hasOwnProperty(t) && t in _s) return Ei[e] = n[t];
    return e;
  }
  var $s = Gr("animationend"), eu = Gr("animationiteration"), nu = Gr("animationstart"), tu = Gr("transitionend"), ru = /* @__PURE__ */ new Map(), lu = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
  function Hn(e, n) {
    ru.set(e, n), x(n, [e]);
  }
  for (var zi = 0; zi < lu.length; zi++) {
    var Ri = lu[zi], xd = Ri.toLowerCase(), wd = Ri[0].toUpperCase() + Ri.slice(1);
    Hn(xd, "on" + wd);
  }
  Hn($s, "onAnimationEnd"), Hn(eu, "onAnimationIteration"), Hn(nu, "onAnimationStart"), Hn("dblclick", "onDoubleClick"), Hn("focusin", "onFocus"), Hn("focusout", "onBlur"), Hn(tu, "onTransitionEnd"), z("onMouseEnter", ["mouseout", "mouseover"]), z("onMouseLeave", ["mouseout", "mouseover"]), z("onPointerEnter", ["pointerout", "pointerover"]), z("onPointerLeave", ["pointerout", "pointerover"]), x("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), x("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), x("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]), x("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), x("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), x("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
  var ir = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), kd = new Set("cancel close invalid load scroll toggle".split(" ").concat(ir));
  function iu(e, n, t) {
    var r = e.type || "unknown-event";
    e.currentTarget = t, xc(r, n, void 0, e), e.currentTarget = null;
  }
  function ou(e, n) {
    n = (n & 4) !== 0;
    for (var t = 0; t < e.length; t++) {
      var r = e[t], l = r.event;
      r = r.listeners;
      e: {
        var i = void 0;
        if (n) for (var s = r.length - 1; 0 <= s; s--) {
          var d = r[s], f = d.instance, y = d.currentTarget;
          if (d = d.listener, f !== i && l.isPropagationStopped()) break e;
          iu(l, d, y), i = f;
        }
        else for (s = 0; s < r.length; s++) {
          if (d = r[s], f = d.instance, y = d.currentTarget, d = d.listener, f !== i && l.isPropagationStopped()) break e;
          iu(l, d, y), i = f;
        }
      }
    }
    if (Fr) throw e = ii, Fr = !1, ii = null, e;
  }
  function ce(e, n) {
    var t = n[Wi];
    t === void 0 && (t = n[Wi] = /* @__PURE__ */ new Set());
    var r = e + "__bubble";
    t.has(r) || (su(n, e, 2, !1), t.add(r));
  }
  function Pi(e, n, t) {
    var r = 0;
    n && (r |= 4), su(t, e, r, n);
  }
  var Yr = "_reactListening" + Math.random().toString(36).slice(2);
  function or(e) {
    if (!e[Yr]) {
      e[Yr] = !0, g.forEach(function(t) {
        t !== "selectionchange" && (kd.has(t) || Pi(t, !1, e), Pi(t, !0, e));
      });
      var n = e.nodeType === 9 ? e : e.ownerDocument;
      n === null || n[Yr] || (n[Yr] = !0, Pi("selectionchange", !1, n));
    }
  }
  function su(e, n, t, r) {
    switch (Ts(n)) {
      case 1:
        var l = Ic;
        break;
      case 4:
        l = Wc;
        break;
      default:
        l = fi;
    }
    t = l.bind(null, n, t, e), l = void 0, !li || n !== "touchstart" && n !== "touchmove" && n !== "wheel" || (l = !0), r ? l !== void 0 ? e.addEventListener(n, t, { capture: !0, passive: l }) : e.addEventListener(n, t, !0) : l !== void 0 ? e.addEventListener(n, t, { passive: l }) : e.addEventListener(n, t, !1);
  }
  function Ti(e, n, t, r, l) {
    var i = r;
    if ((n & 1) === 0 && (n & 2) === 0 && r !== null) e: for (; ; ) {
      if (r === null) return;
      var s = r.tag;
      if (s === 3 || s === 4) {
        var d = r.stateNode.containerInfo;
        if (d === l || d.nodeType === 8 && d.parentNode === l) break;
        if (s === 4) for (s = r.return; s !== null; ) {
          var f = s.tag;
          if ((f === 3 || f === 4) && (f = s.stateNode.containerInfo, f === l || f.nodeType === 8 && f.parentNode === l)) return;
          s = s.return;
        }
        for (; d !== null; ) {
          if (s = tt(d), s === null) return;
          if (f = s.tag, f === 5 || f === 6) {
            r = i = s;
            continue e;
          }
          d = d.parentNode;
        }
      }
      r = r.return;
    }
    fs(function() {
      var y = i, N = ni(t), C = [];
      e: {
        var j = ru.get(e);
        if (j !== void 0) {
          var F = mi, I = e;
          switch (e) {
            case "keypress":
              if (Xr(t) === 0) break e;
            case "keydown":
            case "keyup":
              F = bc;
              break;
            case "focusin":
              I = "focus", F = yi;
              break;
            case "focusout":
              I = "blur", F = yi;
              break;
            case "beforeblur":
            case "afterblur":
              F = yi;
              break;
            case "click":
              if (t.button === 2) break e;
            case "auxclick":
            case "dblclick":
            case "mousedown":
            case "mousemove":
            case "mouseup":
            case "mouseout":
            case "mouseover":
            case "contextmenu":
              F = Fs;
              break;
            case "drag":
            case "dragend":
            case "dragenter":
            case "dragexit":
            case "dragleave":
            case "dragover":
            case "dragstart":
            case "drop":
              F = Uc;
              break;
            case "touchcancel":
            case "touchend":
            case "touchmove":
            case "touchstart":
              F = ed;
              break;
            case $s:
            case eu:
            case nu:
              F = Ac;
              break;
            case tu:
              F = td;
              break;
            case "scroll":
              F = Dc;
              break;
            case "wheel":
              F = ld;
              break;
            case "copy":
            case "cut":
            case "paste":
              F = Xc;
              break;
            case "gotpointercapture":
            case "lostpointercapture":
            case "pointercancel":
            case "pointerdown":
            case "pointermove":
            case "pointerout":
            case "pointerover":
            case "pointerup":
              F = Is;
          }
          var W = (n & 4) !== 0, je = !W && e === "scroll", m = W ? j !== null ? j + "Capture" : null : j;
          W = [];
          for (var p = y, v; p !== null; ) {
            v = p;
            var R = v.stateNode;
            if (v.tag === 5 && R !== null && (v = R, m !== null && (R = At(p, m), R != null && W.push(sr(p, R, v)))), je) break;
            p = p.return;
          }
          0 < W.length && (j = new F(j, I, null, t, N), C.push({ event: j, listeners: W }));
        }
      }
      if ((n & 7) === 0) {
        e: {
          if (j = e === "mouseover" || e === "pointerover", F = e === "mouseout" || e === "pointerout", j && t !== ei && (I = t.relatedTarget || t.fromElement) && (tt(I) || I[zn])) break e;
          if ((F || j) && (j = N.window === N ? N : (j = N.ownerDocument) ? j.defaultView || j.parentWindow : window, F ? (I = t.relatedTarget || t.toElement, F = y, I = I ? tt(I) : null, I !== null && (je = nt(I), I !== je || I.tag !== 5 && I.tag !== 6) && (I = null)) : (F = null, I = y), F !== I)) {
            if (W = Fs, R = "onMouseLeave", m = "onMouseEnter", p = "mouse", (e === "pointerout" || e === "pointerover") && (W = Is, R = "onPointerLeave", m = "onPointerEnter", p = "pointer"), je = F == null ? j : Nt(F), v = I == null ? j : Nt(I), j = new W(R, p + "leave", F, t, N), j.target = je, j.relatedTarget = v, R = null, tt(N) === y && (W = new W(m, p + "enter", I, t, N), W.target = v, W.relatedTarget = je, R = W), je = R, F && I) n: {
              for (W = F, m = I, p = 0, v = W; v; v = St(v)) p++;
              for (v = 0, R = m; R; R = St(R)) v++;
              for (; 0 < p - v; ) W = St(W), p--;
              for (; 0 < v - p; ) m = St(m), v--;
              for (; p--; ) {
                if (W === m || m !== null && W === m.alternate) break n;
                W = St(W), m = St(m);
              }
              W = null;
            }
            else W = null;
            F !== null && uu(C, j, F, W, !1), I !== null && je !== null && uu(C, je, I, W, !0);
          }
        }
        e: {
          if (j = y ? Nt(y) : window, F = j.nodeName && j.nodeName.toLowerCase(), F === "select" || F === "input" && j.type === "file") var D = dd;
          else if (Hs(j)) if (Bs) D = md;
          else {
            D = pd;
            var q = fd;
          }
          else (F = j.nodeName) && F.toLowerCase() === "input" && (j.type === "checkbox" || j.type === "radio") && (D = hd);
          if (D && (D = D(e, y))) {
            As(C, D, t, N);
            break e;
          }
          q && q(e, j, y), e === "focusout" && (q = j._wrapperState) && q.controlled && j.type === "number" && Gl(j, "number", j.value);
        }
        switch (q = y ? Nt(y) : window, e) {
          case "focusin":
            (Hs(q) || q.contentEditable === "true") && (wt = q, Ni = y, lr = null);
            break;
          case "focusout":
            lr = Ni = wt = null;
            break;
          case "mousedown":
            Ci = !0;
            break;
          case "contextmenu":
          case "mouseup":
          case "dragend":
            Ci = !1, bs(C, t, N);
            break;
          case "selectionchange":
            if (yd) break;
          case "keydown":
          case "keyup":
            bs(C, t, N);
        }
        var H;
        if (wi) e: {
          switch (e) {
            case "compositionstart":
              var A = "onCompositionStart";
              break e;
            case "compositionend":
              A = "onCompositionEnd";
              break e;
            case "compositionupdate":
              A = "onCompositionUpdate";
              break e;
          }
          A = void 0;
        }
        else xt ? Us(e, t) && (A = "onCompositionEnd") : e === "keydown" && t.keyCode === 229 && (A = "onCompositionStart");
        A && (Ws && t.locale !== "ko" && (xt || A !== "onCompositionStart" ? A === "onCompositionEnd" && xt && (H = Ls()) : (qn = N, hi = "value" in qn ? qn.value : qn.textContent, xt = !0)), q = br(y, A), 0 < q.length && (A = new Ms(A, e, null, t, N), C.push({ event: A, listeners: q }), H ? A.data = H : (H = qs(t), H !== null && (A.data = H)))), (H = od ? sd(e, t) : ud(e, t)) && (y = br(y, "onBeforeInput"), 0 < y.length && (N = new Ms("onBeforeInput", "beforeinput", null, t, N), C.push({ event: N, listeners: y }), N.data = H));
      }
      ou(C, n);
    });
  }
  function sr(e, n, t) {
    return { instance: e, listener: n, currentTarget: t };
  }
  function br(e, n) {
    for (var t = n + "Capture", r = []; e !== null; ) {
      var l = e, i = l.stateNode;
      l.tag === 5 && i !== null && (l = i, i = At(e, t), i != null && r.unshift(sr(e, i, l)), i = At(e, n), i != null && r.push(sr(e, i, l))), e = e.return;
    }
    return r;
  }
  function St(e) {
    if (e === null) return null;
    do
      e = e.return;
    while (e && e.tag !== 5);
    return e || null;
  }
  function uu(e, n, t, r, l) {
    for (var i = n._reactName, s = []; t !== null && t !== r; ) {
      var d = t, f = d.alternate, y = d.stateNode;
      if (f !== null && f === r) break;
      d.tag === 5 && y !== null && (d = y, l ? (f = At(t, i), f != null && s.unshift(sr(t, f, d))) : l || (f = At(t, i), f != null && s.push(sr(t, f, d)))), t = t.return;
    }
    s.length !== 0 && e.push({ event: n, listeners: s });
  }
  var Sd = /\r\n?/g, jd = /\u0000|\uFFFD/g;
  function au(e) {
    return (typeof e == "string" ? e : "" + e).replace(Sd, `
`).replace(jd, "");
  }
  function _r(e, n, t) {
    if (n = au(n), au(e) !== n && t) throw Error(c(425));
  }
  function $r() {
  }
  var Li = null, Oi = null;
  function Fi(e, n) {
    return e === "textarea" || e === "noscript" || typeof n.children == "string" || typeof n.children == "number" || typeof n.dangerouslySetInnerHTML == "object" && n.dangerouslySetInnerHTML !== null && n.dangerouslySetInnerHTML.__html != null;
  }
  var Mi = typeof setTimeout == "function" ? setTimeout : void 0, Nd = typeof clearTimeout == "function" ? clearTimeout : void 0, cu = typeof Promise == "function" ? Promise : void 0, Cd = typeof queueMicrotask == "function" ? queueMicrotask : typeof cu < "u" ? function(e) {
    return cu.resolve(null).then(e).catch(Ed);
  } : Mi;
  function Ed(e) {
    setTimeout(function() {
      throw e;
    });
  }
  function Ii(e, n) {
    var t = n, r = 0;
    do {
      var l = t.nextSibling;
      if (e.removeChild(t), l && l.nodeType === 8) if (t = l.data, t === "/$") {
        if (r === 0) {
          e.removeChild(l), bt(n);
          return;
        }
        r--;
      } else t !== "$" && t !== "$?" && t !== "$!" || r++;
      t = l;
    } while (t);
    bt(n);
  }
  function An(e) {
    for (; e != null; e = e.nextSibling) {
      var n = e.nodeType;
      if (n === 1 || n === 3) break;
      if (n === 8) {
        if (n = e.data, n === "$" || n === "$!" || n === "$?") break;
        if (n === "/$") return null;
      }
    }
    return e;
  }
  function du(e) {
    e = e.previousSibling;
    for (var n = 0; e; ) {
      if (e.nodeType === 8) {
        var t = e.data;
        if (t === "$" || t === "$!" || t === "$?") {
          if (n === 0) return e;
          n--;
        } else t === "/$" && n++;
      }
      e = e.previousSibling;
    }
    return null;
  }
  var jt = Math.random().toString(36).slice(2), jn = "__reactFiber$" + jt, ur = "__reactProps$" + jt, zn = "__reactContainer$" + jt, Wi = "__reactEvents$" + jt, zd = "__reactListeners$" + jt, Rd = "__reactHandles$" + jt;
  function tt(e) {
    var n = e[jn];
    if (n) return n;
    for (var t = e.parentNode; t; ) {
      if (n = t[zn] || t[jn]) {
        if (t = n.alternate, n.child !== null || t !== null && t.child !== null) for (e = du(e); e !== null; ) {
          if (t = e[jn]) return t;
          e = du(e);
        }
        return n;
      }
      e = t, t = e.parentNode;
    }
    return null;
  }
  function ar(e) {
    return e = e[jn] || e[zn], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
  }
  function Nt(e) {
    if (e.tag === 5 || e.tag === 6) return e.stateNode;
    throw Error(c(33));
  }
  function el(e) {
    return e[ur] || null;
  }
  var Di = [], Ct = -1;
  function Bn(e) {
    return { current: e };
  }
  function de(e) {
    0 > Ct || (e.current = Di[Ct], Di[Ct] = null, Ct--);
  }
  function se(e, n) {
    Ct++, Di[Ct] = e.current, e.current = n;
  }
  var Xn = {}, qe = Bn(Xn), Ge = Bn(!1), rt = Xn;
  function Et(e, n) {
    var t = e.type.contextTypes;
    if (!t) return Xn;
    var r = e.stateNode;
    if (r && r.__reactInternalMemoizedUnmaskedChildContext === n) return r.__reactInternalMemoizedMaskedChildContext;
    var l = {}, i;
    for (i in t) l[i] = n[i];
    return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = n, e.__reactInternalMemoizedMaskedChildContext = l), l;
  }
  function Ye(e) {
    return e = e.childContextTypes, e != null;
  }
  function nl() {
    de(Ge), de(qe);
  }
  function fu(e, n, t) {
    if (qe.current !== Xn) throw Error(c(168));
    se(qe, n), se(Ge, t);
  }
  function pu(e, n, t) {
    var r = e.stateNode;
    if (n = n.childContextTypes, typeof r.getChildContext != "function") return t;
    r = r.getChildContext();
    for (var l in r) if (!(l in n)) throw Error(c(108, oe(e) || "Unknown", l));
    return P({}, t, r);
  }
  function tl(e) {
    return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Xn, rt = qe.current, se(qe, e), se(Ge, Ge.current), !0;
  }
  function hu(e, n, t) {
    var r = e.stateNode;
    if (!r) throw Error(c(169));
    t ? (e = pu(e, n, rt), r.__reactInternalMemoizedMergedChildContext = e, de(Ge), de(qe), se(qe, e)) : de(Ge), se(Ge, t);
  }
  var Rn = null, rl = !1, Vi = !1;
  function mu(e) {
    Rn === null ? Rn = [e] : Rn.push(e);
  }
  function Pd(e) {
    rl = !0, mu(e);
  }
  function Zn() {
    if (!Vi && Rn !== null) {
      Vi = !0;
      var e = 0, n = le;
      try {
        var t = Rn;
        for (le = 1; e < t.length; e++) {
          var r = t[e];
          do
            r = r(!0);
          while (r !== null);
        }
        Rn = null, rl = !1;
      } catch (l) {
        throw Rn !== null && (Rn = Rn.slice(e + 1)), gs(oi, Zn), l;
      } finally {
        le = n, Vi = !1;
      }
    }
    return null;
  }
  var zt = [], Rt = 0, ll = null, il = 0, un = [], an = 0, lt = null, Pn = 1, Tn = "";
  function it(e, n) {
    zt[Rt++] = il, zt[Rt++] = ll, ll = e, il = n;
  }
  function vu(e, n, t) {
    un[an++] = Pn, un[an++] = Tn, un[an++] = lt, lt = e;
    var r = Pn;
    e = Tn;
    var l = 32 - hn(r) - 1;
    r &= ~(1 << l), t += 1;
    var i = 32 - hn(n) + l;
    if (30 < i) {
      var s = l - l % 5;
      i = (r & (1 << s) - 1).toString(32), r >>= s, l -= s, Pn = 1 << 32 - hn(n) + l | t << l | r, Tn = i + e;
    } else Pn = 1 << i | t << l | r, Tn = e;
  }
  function Ui(e) {
    e.return !== null && (it(e, 1), vu(e, 1, 0));
  }
  function qi(e) {
    for (; e === ll; ) ll = zt[--Rt], zt[Rt] = null, il = zt[--Rt], zt[Rt] = null;
    for (; e === lt; ) lt = un[--an], un[an] = null, Tn = un[--an], un[an] = null, Pn = un[--an], un[an] = null;
  }
  var ln = null, on = null, me = !1, vn = null;
  function gu(e, n) {
    var t = pn(5, null, null, 0);
    t.elementType = "DELETED", t.stateNode = n, t.return = e, n = e.deletions, n === null ? (e.deletions = [t], e.flags |= 16) : n.push(t);
  }
  function yu(e, n) {
    switch (e.tag) {
      case 5:
        var t = e.type;
        return n = n.nodeType !== 1 || t.toLowerCase() !== n.nodeName.toLowerCase() ? null : n, n !== null ? (e.stateNode = n, ln = e, on = An(n.firstChild), !0) : !1;
      case 6:
        return n = e.pendingProps === "" || n.nodeType !== 3 ? null : n, n !== null ? (e.stateNode = n, ln = e, on = null, !0) : !1;
      case 13:
        return n = n.nodeType !== 8 ? null : n, n !== null ? (t = lt !== null ? { id: Pn, overflow: Tn } : null, e.memoizedState = { dehydrated: n, treeContext: t, retryLane: 1073741824 }, t = pn(18, null, null, 0), t.stateNode = n, t.return = e, e.child = t, ln = e, on = null, !0) : !1;
      default:
        return !1;
    }
  }
  function Hi(e) {
    return (e.mode & 1) !== 0 && (e.flags & 128) === 0;
  }
  function Ai(e) {
    if (me) {
      var n = on;
      if (n) {
        var t = n;
        if (!yu(e, n)) {
          if (Hi(e)) throw Error(c(418));
          n = An(t.nextSibling);
          var r = ln;
          n && yu(e, n) ? gu(r, t) : (e.flags = e.flags & -4097 | 2, me = !1, ln = e);
        }
      } else {
        if (Hi(e)) throw Error(c(418));
        e.flags = e.flags & -4097 | 2, me = !1, ln = e;
      }
    }
  }
  function xu(e) {
    for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13; ) e = e.return;
    ln = e;
  }
  function ol(e) {
    if (e !== ln) return !1;
    if (!me) return xu(e), me = !0, !1;
    var n;
    if ((n = e.tag !== 3) && !(n = e.tag !== 5) && (n = e.type, n = n !== "head" && n !== "body" && !Fi(e.type, e.memoizedProps)), n && (n = on)) {
      if (Hi(e)) throw wu(), Error(c(418));
      for (; n; ) gu(e, n), n = An(n.nextSibling);
    }
    if (xu(e), e.tag === 13) {
      if (e = e.memoizedState, e = e !== null ? e.dehydrated : null, !e) throw Error(c(317));
      e: {
        for (e = e.nextSibling, n = 0; e; ) {
          if (e.nodeType === 8) {
            var t = e.data;
            if (t === "/$") {
              if (n === 0) {
                on = An(e.nextSibling);
                break e;
              }
              n--;
            } else t !== "$" && t !== "$!" && t !== "$?" || n++;
          }
          e = e.nextSibling;
        }
        on = null;
      }
    } else on = ln ? An(e.stateNode.nextSibling) : null;
    return !0;
  }
  function wu() {
    for (var e = on; e; ) e = An(e.nextSibling);
  }
  function Pt() {
    on = ln = null, me = !1;
  }
  function Bi(e) {
    vn === null ? vn = [e] : vn.push(e);
  }
  var Td = fe.ReactCurrentBatchConfig;
  function cr(e, n, t) {
    if (e = t.ref, e !== null && typeof e != "function" && typeof e != "object") {
      if (t._owner) {
        if (t = t._owner, t) {
          if (t.tag !== 1) throw Error(c(309));
          var r = t.stateNode;
        }
        if (!r) throw Error(c(147, e));
        var l = r, i = "" + e;
        return n !== null && n.ref !== null && typeof n.ref == "function" && n.ref._stringRef === i ? n.ref : (n = function(s) {
          var d = l.refs;
          s === null ? delete d[i] : d[i] = s;
        }, n._stringRef = i, n);
      }
      if (typeof e != "string") throw Error(c(284));
      if (!t._owner) throw Error(c(290, e));
    }
    return e;
  }
  function sl(e, n) {
    throw e = Object.prototype.toString.call(n), Error(c(31, e === "[object Object]" ? "object with keys {" + Object.keys(n).join(", ") + "}" : e));
  }
  function ku(e) {
    var n = e._init;
    return n(e._payload);
  }
  function Su(e) {
    function n(m, p) {
      if (e) {
        var v = m.deletions;
        v === null ? (m.deletions = [p], m.flags |= 16) : v.push(p);
      }
    }
    function t(m, p) {
      if (!e) return null;
      for (; p !== null; ) n(m, p), p = p.sibling;
      return null;
    }
    function r(m, p) {
      for (m = /* @__PURE__ */ new Map(); p !== null; ) p.key !== null ? m.set(p.key, p) : m.set(p.index, p), p = p.sibling;
      return m;
    }
    function l(m, p) {
      return m = $n(m, p), m.index = 0, m.sibling = null, m;
    }
    function i(m, p, v) {
      return m.index = v, e ? (v = m.alternate, v !== null ? (v = v.index, v < p ? (m.flags |= 2, p) : v) : (m.flags |= 2, p)) : (m.flags |= 1048576, p);
    }
    function s(m) {
      return e && m.alternate === null && (m.flags |= 2), m;
    }
    function d(m, p, v, R) {
      return p === null || p.tag !== 6 ? (p = Io(v, m.mode, R), p.return = m, p) : (p = l(p, v), p.return = m, p);
    }
    function f(m, p, v, R) {
      var D = v.type;
      return D === pe ? N(m, p, v.props.children, R, v.key) : p !== null && (p.elementType === D || typeof D == "object" && D !== null && D.$$typeof === Ce && ku(D) === p.type) ? (R = l(p, v.props), R.ref = cr(m, p, v), R.return = m, R) : (R = Ll(v.type, v.key, v.props, null, m.mode, R), R.ref = cr(m, p, v), R.return = m, R);
    }
    function y(m, p, v, R) {
      return p === null || p.tag !== 4 || p.stateNode.containerInfo !== v.containerInfo || p.stateNode.implementation !== v.implementation ? (p = Wo(v, m.mode, R), p.return = m, p) : (p = l(p, v.children || []), p.return = m, p);
    }
    function N(m, p, v, R, D) {
      return p === null || p.tag !== 7 ? (p = pt(v, m.mode, R, D), p.return = m, p) : (p = l(p, v), p.return = m, p);
    }
    function C(m, p, v) {
      if (typeof p == "string" && p !== "" || typeof p == "number") return p = Io("" + p, m.mode, v), p.return = m, p;
      if (typeof p == "object" && p !== null) {
        switch (p.$$typeof) {
          case Te:
            return v = Ll(p.type, p.key, p.props, null, m.mode, v), v.ref = cr(m, null, p), v.return = m, v;
          case ke:
            return p = Wo(p, m.mode, v), p.return = m, p;
          case Ce:
            var R = p._init;
            return C(m, R(p._payload), v);
        }
        if (Ut(p) || T(p)) return p = pt(p, m.mode, v, null), p.return = m, p;
        sl(m, p);
      }
      return null;
    }
    function j(m, p, v, R) {
      var D = p !== null ? p.key : null;
      if (typeof v == "string" && v !== "" || typeof v == "number") return D !== null ? null : d(m, p, "" + v, R);
      if (typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case Te:
            return v.key === D ? f(m, p, v, R) : null;
          case ke:
            return v.key === D ? y(m, p, v, R) : null;
          case Ce:
            return D = v._init, j(
              m,
              p,
              D(v._payload),
              R
            );
        }
        if (Ut(v) || T(v)) return D !== null ? null : N(m, p, v, R, null);
        sl(m, v);
      }
      return null;
    }
    function F(m, p, v, R, D) {
      if (typeof R == "string" && R !== "" || typeof R == "number") return m = m.get(v) || null, d(p, m, "" + R, D);
      if (typeof R == "object" && R !== null) {
        switch (R.$$typeof) {
          case Te:
            return m = m.get(R.key === null ? v : R.key) || null, f(p, m, R, D);
          case ke:
            return m = m.get(R.key === null ? v : R.key) || null, y(p, m, R, D);
          case Ce:
            var q = R._init;
            return F(m, p, v, q(R._payload), D);
        }
        if (Ut(R) || T(R)) return m = m.get(v) || null, N(p, m, R, D, null);
        sl(p, R);
      }
      return null;
    }
    function I(m, p, v, R) {
      for (var D = null, q = null, H = p, A = p = 0, Me = null; H !== null && A < v.length; A++) {
        H.index > A ? (Me = H, H = null) : Me = H.sibling;
        var te = j(m, H, v[A], R);
        if (te === null) {
          H === null && (H = Me);
          break;
        }
        e && H && te.alternate === null && n(m, H), p = i(te, p, A), q === null ? D = te : q.sibling = te, q = te, H = Me;
      }
      if (A === v.length) return t(m, H), me && it(m, A), D;
      if (H === null) {
        for (; A < v.length; A++) H = C(m, v[A], R), H !== null && (p = i(H, p, A), q === null ? D = H : q.sibling = H, q = H);
        return me && it(m, A), D;
      }
      for (H = r(m, H); A < v.length; A++) Me = F(H, m, A, v[A], R), Me !== null && (e && Me.alternate !== null && H.delete(Me.key === null ? A : Me.key), p = i(Me, p, A), q === null ? D = Me : q.sibling = Me, q = Me);
      return e && H.forEach(function(et) {
        return n(m, et);
      }), me && it(m, A), D;
    }
    function W(m, p, v, R) {
      var D = T(v);
      if (typeof D != "function") throw Error(c(150));
      if (v = D.call(v), v == null) throw Error(c(151));
      for (var q = D = null, H = p, A = p = 0, Me = null, te = v.next(); H !== null && !te.done; A++, te = v.next()) {
        H.index > A ? (Me = H, H = null) : Me = H.sibling;
        var et = j(m, H, te.value, R);
        if (et === null) {
          H === null && (H = Me);
          break;
        }
        e && H && et.alternate === null && n(m, H), p = i(et, p, A), q === null ? D = et : q.sibling = et, q = et, H = Me;
      }
      if (te.done) return t(
        m,
        H
      ), me && it(m, A), D;
      if (H === null) {
        for (; !te.done; A++, te = v.next()) te = C(m, te.value, R), te !== null && (p = i(te, p, A), q === null ? D = te : q.sibling = te, q = te);
        return me && it(m, A), D;
      }
      for (H = r(m, H); !te.done; A++, te = v.next()) te = F(H, m, A, te.value, R), te !== null && (e && te.alternate !== null && H.delete(te.key === null ? A : te.key), p = i(te, p, A), q === null ? D = te : q.sibling = te, q = te);
      return e && H.forEach(function(cf) {
        return n(m, cf);
      }), me && it(m, A), D;
    }
    function je(m, p, v, R) {
      if (typeof v == "object" && v !== null && v.type === pe && v.key === null && (v = v.props.children), typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case Te:
            e: {
              for (var D = v.key, q = p; q !== null; ) {
                if (q.key === D) {
                  if (D = v.type, D === pe) {
                    if (q.tag === 7) {
                      t(m, q.sibling), p = l(q, v.props.children), p.return = m, m = p;
                      break e;
                    }
                  } else if (q.elementType === D || typeof D == "object" && D !== null && D.$$typeof === Ce && ku(D) === q.type) {
                    t(m, q.sibling), p = l(q, v.props), p.ref = cr(m, q, v), p.return = m, m = p;
                    break e;
                  }
                  t(m, q);
                  break;
                } else n(m, q);
                q = q.sibling;
              }
              v.type === pe ? (p = pt(v.props.children, m.mode, R, v.key), p.return = m, m = p) : (R = Ll(v.type, v.key, v.props, null, m.mode, R), R.ref = cr(m, p, v), R.return = m, m = R);
            }
            return s(m);
          case ke:
            e: {
              for (q = v.key; p !== null; ) {
                if (p.key === q) if (p.tag === 4 && p.stateNode.containerInfo === v.containerInfo && p.stateNode.implementation === v.implementation) {
                  t(m, p.sibling), p = l(p, v.children || []), p.return = m, m = p;
                  break e;
                } else {
                  t(m, p);
                  break;
                }
                else n(m, p);
                p = p.sibling;
              }
              p = Wo(v, m.mode, R), p.return = m, m = p;
            }
            return s(m);
          case Ce:
            return q = v._init, je(m, p, q(v._payload), R);
        }
        if (Ut(v)) return I(m, p, v, R);
        if (T(v)) return W(m, p, v, R);
        sl(m, v);
      }
      return typeof v == "string" && v !== "" || typeof v == "number" ? (v = "" + v, p !== null && p.tag === 6 ? (t(m, p.sibling), p = l(p, v), p.return = m, m = p) : (t(m, p), p = Io(v, m.mode, R), p.return = m, m = p), s(m)) : t(m, p);
    }
    return je;
  }
  var Tt = Su(!0), ju = Su(!1), ul = Bn(null), al = null, Lt = null, Xi = null;
  function Zi() {
    Xi = Lt = al = null;
  }
  function Ji(e) {
    var n = ul.current;
    de(ul), e._currentValue = n;
  }
  function Ki(e, n, t) {
    for (; e !== null; ) {
      var r = e.alternate;
      if ((e.childLanes & n) !== n ? (e.childLanes |= n, r !== null && (r.childLanes |= n)) : r !== null && (r.childLanes & n) !== n && (r.childLanes |= n), e === t) break;
      e = e.return;
    }
  }
  function Ot(e, n) {
    al = e, Xi = Lt = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & n) !== 0 && (be = !0), e.firstContext = null);
  }
  function cn(e) {
    var n = e._currentValue;
    if (Xi !== e) if (e = { context: e, memoizedValue: n, next: null }, Lt === null) {
      if (al === null) throw Error(c(308));
      Lt = e, al.dependencies = { lanes: 0, firstContext: e };
    } else Lt = Lt.next = e;
    return n;
  }
  var ot = null;
  function Qi(e) {
    ot === null ? ot = [e] : ot.push(e);
  }
  function Nu(e, n, t, r) {
    var l = n.interleaved;
    return l === null ? (t.next = t, Qi(n)) : (t.next = l.next, l.next = t), n.interleaved = t, Ln(e, r);
  }
  function Ln(e, n) {
    e.lanes |= n;
    var t = e.alternate;
    for (t !== null && (t.lanes |= n), t = e, e = e.return; e !== null; ) e.childLanes |= n, t = e.alternate, t !== null && (t.childLanes |= n), t = e, e = e.return;
    return t.tag === 3 ? t.stateNode : null;
  }
  var Jn = !1;
  function Gi(e) {
    e.updateQueue = { baseState: e.memoizedState, firstBaseUpdate: null, lastBaseUpdate: null, shared: { pending: null, interleaved: null, lanes: 0 }, effects: null };
  }
  function Cu(e, n) {
    e = e.updateQueue, n.updateQueue === e && (n.updateQueue = { baseState: e.baseState, firstBaseUpdate: e.firstBaseUpdate, lastBaseUpdate: e.lastBaseUpdate, shared: e.shared, effects: e.effects });
  }
  function On(e, n) {
    return { eventTime: e, lane: n, tag: 0, payload: null, callback: null, next: null };
  }
  function Kn(e, n, t) {
    var r = e.updateQueue;
    if (r === null) return null;
    if (r = r.shared, ($ & 2) !== 0) {
      var l = r.pending;
      return l === null ? n.next = n : (n.next = l.next, l.next = n), r.pending = n, Ln(e, t);
    }
    return l = r.interleaved, l === null ? (n.next = n, Qi(r)) : (n.next = l.next, l.next = n), r.interleaved = n, Ln(e, t);
  }
  function cl(e, n, t) {
    if (n = n.updateQueue, n !== null && (n = n.shared, (t & 4194240) !== 0)) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, ai(e, t);
    }
  }
  function Eu(e, n) {
    var t = e.updateQueue, r = e.alternate;
    if (r !== null && (r = r.updateQueue, t === r)) {
      var l = null, i = null;
      if (t = t.firstBaseUpdate, t !== null) {
        do {
          var s = { eventTime: t.eventTime, lane: t.lane, tag: t.tag, payload: t.payload, callback: t.callback, next: null };
          i === null ? l = i = s : i = i.next = s, t = t.next;
        } while (t !== null);
        i === null ? l = i = n : i = i.next = n;
      } else l = i = n;
      t = { baseState: r.baseState, firstBaseUpdate: l, lastBaseUpdate: i, shared: r.shared, effects: r.effects }, e.updateQueue = t;
      return;
    }
    e = t.lastBaseUpdate, e === null ? t.firstBaseUpdate = n : e.next = n, t.lastBaseUpdate = n;
  }
  function dl(e, n, t, r) {
    var l = e.updateQueue;
    Jn = !1;
    var i = l.firstBaseUpdate, s = l.lastBaseUpdate, d = l.shared.pending;
    if (d !== null) {
      l.shared.pending = null;
      var f = d, y = f.next;
      f.next = null, s === null ? i = y : s.next = y, s = f;
      var N = e.alternate;
      N !== null && (N = N.updateQueue, d = N.lastBaseUpdate, d !== s && (d === null ? N.firstBaseUpdate = y : d.next = y, N.lastBaseUpdate = f));
    }
    if (i !== null) {
      var C = l.baseState;
      s = 0, N = y = f = null, d = i;
      do {
        var j = d.lane, F = d.eventTime;
        if ((r & j) === j) {
          N !== null && (N = N.next = {
            eventTime: F,
            lane: 0,
            tag: d.tag,
            payload: d.payload,
            callback: d.callback,
            next: null
          });
          e: {
            var I = e, W = d;
            switch (j = n, F = t, W.tag) {
              case 1:
                if (I = W.payload, typeof I == "function") {
                  C = I.call(F, C, j);
                  break e;
                }
                C = I;
                break e;
              case 3:
                I.flags = I.flags & -65537 | 128;
              case 0:
                if (I = W.payload, j = typeof I == "function" ? I.call(F, C, j) : I, j == null) break e;
                C = P({}, C, j);
                break e;
              case 2:
                Jn = !0;
            }
          }
          d.callback !== null && d.lane !== 0 && (e.flags |= 64, j = l.effects, j === null ? l.effects = [d] : j.push(d));
        } else F = { eventTime: F, lane: j, tag: d.tag, payload: d.payload, callback: d.callback, next: null }, N === null ? (y = N = F, f = C) : N = N.next = F, s |= j;
        if (d = d.next, d === null) {
          if (d = l.shared.pending, d === null) break;
          j = d, d = j.next, j.next = null, l.lastBaseUpdate = j, l.shared.pending = null;
        }
      } while (!0);
      if (N === null && (f = C), l.baseState = f, l.firstBaseUpdate = y, l.lastBaseUpdate = N, n = l.shared.interleaved, n !== null) {
        l = n;
        do
          s |= l.lane, l = l.next;
        while (l !== n);
      } else i === null && (l.shared.lanes = 0);
      at |= s, e.lanes = s, e.memoizedState = C;
    }
  }
  function zu(e, n, t) {
    if (e = n.effects, n.effects = null, e !== null) for (n = 0; n < e.length; n++) {
      var r = e[n], l = r.callback;
      if (l !== null) {
        if (r.callback = null, r = t, typeof l != "function") throw Error(c(191, l));
        l.call(r);
      }
    }
  }
  var dr = {}, Nn = Bn(dr), fr = Bn(dr), pr = Bn(dr);
  function st(e) {
    if (e === dr) throw Error(c(174));
    return e;
  }
  function Yi(e, n) {
    switch (se(pr, n), se(fr, e), se(Nn, dr), e = n.nodeType, e) {
      case 9:
      case 11:
        n = (n = n.documentElement) ? n.namespaceURI : bl(null, "");
        break;
      default:
        e = e === 8 ? n.parentNode : n, n = e.namespaceURI || null, e = e.tagName, n = bl(n, e);
    }
    de(Nn), se(Nn, n);
  }
  function Ft() {
    de(Nn), de(fr), de(pr);
  }
  function Ru(e) {
    st(pr.current);
    var n = st(Nn.current), t = bl(n, e.type);
    n !== t && (se(fr, e), se(Nn, t));
  }
  function bi(e) {
    fr.current === e && (de(Nn), de(fr));
  }
  var ye = Bn(0);
  function fl(e) {
    for (var n = e; n !== null; ) {
      if (n.tag === 13) {
        var t = n.memoizedState;
        if (t !== null && (t = t.dehydrated, t === null || t.data === "$?" || t.data === "$!")) return n;
      } else if (n.tag === 19 && n.memoizedProps.revealOrder !== void 0) {
        if ((n.flags & 128) !== 0) return n;
      } else if (n.child !== null) {
        n.child.return = n, n = n.child;
        continue;
      }
      if (n === e) break;
      for (; n.sibling === null; ) {
        if (n.return === null || n.return === e) return null;
        n = n.return;
      }
      n.sibling.return = n.return, n = n.sibling;
    }
    return null;
  }
  var _i = [];
  function $i() {
    for (var e = 0; e < _i.length; e++) _i[e]._workInProgressVersionPrimary = null;
    _i.length = 0;
  }
  var pl = fe.ReactCurrentDispatcher, eo = fe.ReactCurrentBatchConfig, ut = 0, xe = null, Re = null, Oe = null, hl = !1, hr = !1, mr = 0, Ld = 0;
  function He() {
    throw Error(c(321));
  }
  function no(e, n) {
    if (n === null) return !1;
    for (var t = 0; t < n.length && t < e.length; t++) if (!mn(e[t], n[t])) return !1;
    return !0;
  }
  function to(e, n, t, r, l, i) {
    if (ut = i, xe = n, n.memoizedState = null, n.updateQueue = null, n.lanes = 0, pl.current = e === null || e.memoizedState === null ? Id : Wd, e = t(r, l), hr) {
      i = 0;
      do {
        if (hr = !1, mr = 0, 25 <= i) throw Error(c(301));
        i += 1, Oe = Re = null, n.updateQueue = null, pl.current = Dd, e = t(r, l);
      } while (hr);
    }
    if (pl.current = gl, n = Re !== null && Re.next !== null, ut = 0, Oe = Re = xe = null, hl = !1, n) throw Error(c(300));
    return e;
  }
  function ro() {
    var e = mr !== 0;
    return mr = 0, e;
  }
  function Cn() {
    var e = { memoizedState: null, baseState: null, baseQueue: null, queue: null, next: null };
    return Oe === null ? xe.memoizedState = Oe = e : Oe = Oe.next = e, Oe;
  }
  function dn() {
    if (Re === null) {
      var e = xe.alternate;
      e = e !== null ? e.memoizedState : null;
    } else e = Re.next;
    var n = Oe === null ? xe.memoizedState : Oe.next;
    if (n !== null) Oe = n, Re = e;
    else {
      if (e === null) throw Error(c(310));
      Re = e, e = { memoizedState: Re.memoizedState, baseState: Re.baseState, baseQueue: Re.baseQueue, queue: Re.queue, next: null }, Oe === null ? xe.memoizedState = Oe = e : Oe = Oe.next = e;
    }
    return Oe;
  }
  function vr(e, n) {
    return typeof n == "function" ? n(e) : n;
  }
  function lo(e) {
    var n = dn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = Re, l = r.baseQueue, i = t.pending;
    if (i !== null) {
      if (l !== null) {
        var s = l.next;
        l.next = i.next, i.next = s;
      }
      r.baseQueue = l = i, t.pending = null;
    }
    if (l !== null) {
      i = l.next, r = r.baseState;
      var d = s = null, f = null, y = i;
      do {
        var N = y.lane;
        if ((ut & N) === N) f !== null && (f = f.next = { lane: 0, action: y.action, hasEagerState: y.hasEagerState, eagerState: y.eagerState, next: null }), r = y.hasEagerState ? y.eagerState : e(r, y.action);
        else {
          var C = {
            lane: N,
            action: y.action,
            hasEagerState: y.hasEagerState,
            eagerState: y.eagerState,
            next: null
          };
          f === null ? (d = f = C, s = r) : f = f.next = C, xe.lanes |= N, at |= N;
        }
        y = y.next;
      } while (y !== null && y !== i);
      f === null ? s = r : f.next = d, mn(r, n.memoizedState) || (be = !0), n.memoizedState = r, n.baseState = s, n.baseQueue = f, t.lastRenderedState = r;
    }
    if (e = t.interleaved, e !== null) {
      l = e;
      do
        i = l.lane, xe.lanes |= i, at |= i, l = l.next;
      while (l !== e);
    } else l === null && (t.lanes = 0);
    return [n.memoizedState, t.dispatch];
  }
  function io(e) {
    var n = dn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = t.dispatch, l = t.pending, i = n.memoizedState;
    if (l !== null) {
      t.pending = null;
      var s = l = l.next;
      do
        i = e(i, s.action), s = s.next;
      while (s !== l);
      mn(i, n.memoizedState) || (be = !0), n.memoizedState = i, n.baseQueue === null && (n.baseState = i), t.lastRenderedState = i;
    }
    return [i, r];
  }
  function Pu() {
  }
  function Tu(e, n) {
    var t = xe, r = dn(), l = n(), i = !mn(r.memoizedState, l);
    if (i && (r.memoizedState = l, be = !0), r = r.queue, oo(Fu.bind(null, t, r, e), [e]), r.getSnapshot !== n || i || Oe !== null && Oe.memoizedState.tag & 1) {
      if (t.flags |= 2048, gr(9, Ou.bind(null, t, r, l, n), void 0, null), Fe === null) throw Error(c(349));
      (ut & 30) !== 0 || Lu(t, n, l);
    }
    return l;
  }
  function Lu(e, n, t) {
    e.flags |= 16384, e = { getSnapshot: n, value: t }, n = xe.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, xe.updateQueue = n, n.stores = [e]) : (t = n.stores, t === null ? n.stores = [e] : t.push(e));
  }
  function Ou(e, n, t, r) {
    n.value = t, n.getSnapshot = r, Mu(n) && Iu(e);
  }
  function Fu(e, n, t) {
    return t(function() {
      Mu(n) && Iu(e);
    });
  }
  function Mu(e) {
    var n = e.getSnapshot;
    e = e.value;
    try {
      var t = n();
      return !mn(e, t);
    } catch {
      return !0;
    }
  }
  function Iu(e) {
    var n = Ln(e, 1);
    n !== null && wn(n, e, 1, -1);
  }
  function Wu(e) {
    var n = Cn();
    return typeof e == "function" && (e = e()), n.memoizedState = n.baseState = e, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: vr, lastRenderedState: e }, n.queue = e, e = e.dispatch = Md.bind(null, xe, e), [n.memoizedState, e];
  }
  function gr(e, n, t, r) {
    return e = { tag: e, create: n, destroy: t, deps: r, next: null }, n = xe.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, xe.updateQueue = n, n.lastEffect = e.next = e) : (t = n.lastEffect, t === null ? n.lastEffect = e.next = e : (r = t.next, t.next = e, e.next = r, n.lastEffect = e)), e;
  }
  function Du() {
    return dn().memoizedState;
  }
  function ml(e, n, t, r) {
    var l = Cn();
    xe.flags |= e, l.memoizedState = gr(1 | n, t, void 0, r === void 0 ? null : r);
  }
  function vl(e, n, t, r) {
    var l = dn();
    r = r === void 0 ? null : r;
    var i = void 0;
    if (Re !== null) {
      var s = Re.memoizedState;
      if (i = s.destroy, r !== null && no(r, s.deps)) {
        l.memoizedState = gr(n, t, i, r);
        return;
      }
    }
    xe.flags |= e, l.memoizedState = gr(1 | n, t, i, r);
  }
  function Vu(e, n) {
    return ml(8390656, 8, e, n);
  }
  function oo(e, n) {
    return vl(2048, 8, e, n);
  }
  function Uu(e, n) {
    return vl(4, 2, e, n);
  }
  function qu(e, n) {
    return vl(4, 4, e, n);
  }
  function Hu(e, n) {
    if (typeof n == "function") return e = e(), n(e), function() {
      n(null);
    };
    if (n != null) return e = e(), n.current = e, function() {
      n.current = null;
    };
  }
  function Au(e, n, t) {
    return t = t != null ? t.concat([e]) : null, vl(4, 4, Hu.bind(null, n, e), t);
  }
  function so() {
  }
  function Bu(e, n) {
    var t = dn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && no(n, r[1]) ? r[0] : (t.memoizedState = [e, n], e);
  }
  function Xu(e, n) {
    var t = dn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && no(n, r[1]) ? r[0] : (e = e(), t.memoizedState = [e, n], e);
  }
  function Zu(e, n, t) {
    return (ut & 21) === 0 ? (e.baseState && (e.baseState = !1, be = !0), e.memoizedState = t) : (mn(t, n) || (t = ks(), xe.lanes |= t, at |= t, e.baseState = !0), n);
  }
  function Od(e, n) {
    var t = le;
    le = t !== 0 && 4 > t ? t : 4, e(!0);
    var r = eo.transition;
    eo.transition = {};
    try {
      e(!1), n();
    } finally {
      le = t, eo.transition = r;
    }
  }
  function Ju() {
    return dn().memoizedState;
  }
  function Fd(e, n, t) {
    var r = bn(e);
    if (t = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null }, Ku(e)) Qu(n, t);
    else if (t = Nu(e, n, t, r), t !== null) {
      var l = Qe();
      wn(t, e, r, l), Gu(t, n, r);
    }
  }
  function Md(e, n, t) {
    var r = bn(e), l = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null };
    if (Ku(e)) Qu(n, l);
    else {
      var i = e.alternate;
      if (e.lanes === 0 && (i === null || i.lanes === 0) && (i = n.lastRenderedReducer, i !== null)) try {
        var s = n.lastRenderedState, d = i(s, t);
        if (l.hasEagerState = !0, l.eagerState = d, mn(d, s)) {
          var f = n.interleaved;
          f === null ? (l.next = l, Qi(n)) : (l.next = f.next, f.next = l), n.interleaved = l;
          return;
        }
      } catch {
      } finally {
      }
      t = Nu(e, n, l, r), t !== null && (l = Qe(), wn(t, e, r, l), Gu(t, n, r));
    }
  }
  function Ku(e) {
    var n = e.alternate;
    return e === xe || n !== null && n === xe;
  }
  function Qu(e, n) {
    hr = hl = !0;
    var t = e.pending;
    t === null ? n.next = n : (n.next = t.next, t.next = n), e.pending = n;
  }
  function Gu(e, n, t) {
    if ((t & 4194240) !== 0) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, ai(e, t);
    }
  }
  var gl = { readContext: cn, useCallback: He, useContext: He, useEffect: He, useImperativeHandle: He, useInsertionEffect: He, useLayoutEffect: He, useMemo: He, useReducer: He, useRef: He, useState: He, useDebugValue: He, useDeferredValue: He, useTransition: He, useMutableSource: He, useSyncExternalStore: He, useId: He, unstable_isNewReconciler: !1 }, Id = { readContext: cn, useCallback: function(e, n) {
    return Cn().memoizedState = [e, n === void 0 ? null : n], e;
  }, useContext: cn, useEffect: Vu, useImperativeHandle: function(e, n, t) {
    return t = t != null ? t.concat([e]) : null, ml(
      4194308,
      4,
      Hu.bind(null, n, e),
      t
    );
  }, useLayoutEffect: function(e, n) {
    return ml(4194308, 4, e, n);
  }, useInsertionEffect: function(e, n) {
    return ml(4, 2, e, n);
  }, useMemo: function(e, n) {
    var t = Cn();
    return n = n === void 0 ? null : n, e = e(), t.memoizedState = [e, n], e;
  }, useReducer: function(e, n, t) {
    var r = Cn();
    return n = t !== void 0 ? t(n) : n, r.memoizedState = r.baseState = n, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: e, lastRenderedState: n }, r.queue = e, e = e.dispatch = Fd.bind(null, xe, e), [r.memoizedState, e];
  }, useRef: function(e) {
    var n = Cn();
    return e = { current: e }, n.memoizedState = e;
  }, useState: Wu, useDebugValue: so, useDeferredValue: function(e) {
    return Cn().memoizedState = e;
  }, useTransition: function() {
    var e = Wu(!1), n = e[0];
    return e = Od.bind(null, e[1]), Cn().memoizedState = e, [n, e];
  }, useMutableSource: function() {
  }, useSyncExternalStore: function(e, n, t) {
    var r = xe, l = Cn();
    if (me) {
      if (t === void 0) throw Error(c(407));
      t = t();
    } else {
      if (t = n(), Fe === null) throw Error(c(349));
      (ut & 30) !== 0 || Lu(r, n, t);
    }
    l.memoizedState = t;
    var i = { value: t, getSnapshot: n };
    return l.queue = i, Vu(Fu.bind(
      null,
      r,
      i,
      e
    ), [e]), r.flags |= 2048, gr(9, Ou.bind(null, r, i, t, n), void 0, null), t;
  }, useId: function() {
    var e = Cn(), n = Fe.identifierPrefix;
    if (me) {
      var t = Tn, r = Pn;
      t = (r & ~(1 << 32 - hn(r) - 1)).toString(32) + t, n = ":" + n + "R" + t, t = mr++, 0 < t && (n += "H" + t.toString(32)), n += ":";
    } else t = Ld++, n = ":" + n + "r" + t.toString(32) + ":";
    return e.memoizedState = n;
  }, unstable_isNewReconciler: !1 }, Wd = {
    readContext: cn,
    useCallback: Bu,
    useContext: cn,
    useEffect: oo,
    useImperativeHandle: Au,
    useInsertionEffect: Uu,
    useLayoutEffect: qu,
    useMemo: Xu,
    useReducer: lo,
    useRef: Du,
    useState: function() {
      return lo(vr);
    },
    useDebugValue: so,
    useDeferredValue: function(e) {
      var n = dn();
      return Zu(n, Re.memoizedState, e);
    },
    useTransition: function() {
      var e = lo(vr)[0], n = dn().memoizedState;
      return [e, n];
    },
    useMutableSource: Pu,
    useSyncExternalStore: Tu,
    useId: Ju,
    unstable_isNewReconciler: !1
  }, Dd = { readContext: cn, useCallback: Bu, useContext: cn, useEffect: oo, useImperativeHandle: Au, useInsertionEffect: Uu, useLayoutEffect: qu, useMemo: Xu, useReducer: io, useRef: Du, useState: function() {
    return io(vr);
  }, useDebugValue: so, useDeferredValue: function(e) {
    var n = dn();
    return Re === null ? n.memoizedState = e : Zu(n, Re.memoizedState, e);
  }, useTransition: function() {
    var e = io(vr)[0], n = dn().memoizedState;
    return [e, n];
  }, useMutableSource: Pu, useSyncExternalStore: Tu, useId: Ju, unstable_isNewReconciler: !1 };
  function gn(e, n) {
    if (e && e.defaultProps) {
      n = P({}, n), e = e.defaultProps;
      for (var t in e) n[t] === void 0 && (n[t] = e[t]);
      return n;
    }
    return n;
  }
  function uo(e, n, t, r) {
    n = e.memoizedState, t = t(r, n), t = t == null ? n : P({}, n, t), e.memoizedState = t, e.lanes === 0 && (e.updateQueue.baseState = t);
  }
  var yl = { isMounted: function(e) {
    return (e = e._reactInternals) ? nt(e) === e : !1;
  }, enqueueSetState: function(e, n, t) {
    e = e._reactInternals;
    var r = Qe(), l = bn(e), i = On(r, l);
    i.payload = n, t != null && (i.callback = t), n = Kn(e, i, l), n !== null && (wn(n, e, l, r), cl(n, e, l));
  }, enqueueReplaceState: function(e, n, t) {
    e = e._reactInternals;
    var r = Qe(), l = bn(e), i = On(r, l);
    i.tag = 1, i.payload = n, t != null && (i.callback = t), n = Kn(e, i, l), n !== null && (wn(n, e, l, r), cl(n, e, l));
  }, enqueueForceUpdate: function(e, n) {
    e = e._reactInternals;
    var t = Qe(), r = bn(e), l = On(t, r);
    l.tag = 2, n != null && (l.callback = n), n = Kn(e, l, r), n !== null && (wn(n, e, r, t), cl(n, e, r));
  } };
  function Yu(e, n, t, r, l, i, s) {
    return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, i, s) : n.prototype && n.prototype.isPureReactComponent ? !rr(t, r) || !rr(l, i) : !0;
  }
  function bu(e, n, t) {
    var r = !1, l = Xn, i = n.contextType;
    return typeof i == "object" && i !== null ? i = cn(i) : (l = Ye(n) ? rt : qe.current, r = n.contextTypes, i = (r = r != null) ? Et(e, l) : Xn), n = new n(t, i), e.memoizedState = n.state !== null && n.state !== void 0 ? n.state : null, n.updater = yl, e.stateNode = n, n._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = l, e.__reactInternalMemoizedMaskedChildContext = i), n;
  }
  function _u(e, n, t, r) {
    e = n.state, typeof n.componentWillReceiveProps == "function" && n.componentWillReceiveProps(t, r), typeof n.UNSAFE_componentWillReceiveProps == "function" && n.UNSAFE_componentWillReceiveProps(t, r), n.state !== e && yl.enqueueReplaceState(n, n.state, null);
  }
  function ao(e, n, t, r) {
    var l = e.stateNode;
    l.props = t, l.state = e.memoizedState, l.refs = {}, Gi(e);
    var i = n.contextType;
    typeof i == "object" && i !== null ? l.context = cn(i) : (i = Ye(n) ? rt : qe.current, l.context = Et(e, i)), l.state = e.memoizedState, i = n.getDerivedStateFromProps, typeof i == "function" && (uo(e, n, i, t), l.state = e.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof l.getSnapshotBeforeUpdate == "function" || typeof l.UNSAFE_componentWillMount != "function" && typeof l.componentWillMount != "function" || (n = l.state, typeof l.componentWillMount == "function" && l.componentWillMount(), typeof l.UNSAFE_componentWillMount == "function" && l.UNSAFE_componentWillMount(), n !== l.state && yl.enqueueReplaceState(l, l.state, null), dl(e, t, l, r), l.state = e.memoizedState), typeof l.componentDidMount == "function" && (e.flags |= 4194308);
  }
  function Mt(e, n) {
    try {
      var t = "", r = n;
      do
        t += ee(r), r = r.return;
      while (r);
      var l = t;
    } catch (i) {
      l = `
Error generating stack: ` + i.message + `
` + i.stack;
    }
    return { value: e, source: n, stack: l, digest: null };
  }
  function co(e, n, t) {
    return { value: e, source: null, stack: t ?? null, digest: n ?? null };
  }
  function fo(e, n) {
    try {
      console.error(n.value);
    } catch (t) {
      setTimeout(function() {
        throw t;
      });
    }
  }
  var Vd = typeof WeakMap == "function" ? WeakMap : Map;
  function $u(e, n, t) {
    t = On(-1, t), t.tag = 3, t.payload = { element: null };
    var r = n.value;
    return t.callback = function() {
      Cl || (Cl = !0, zo = r), fo(e, n);
    }, t;
  }
  function ea(e, n, t) {
    t = On(-1, t), t.tag = 3;
    var r = e.type.getDerivedStateFromError;
    if (typeof r == "function") {
      var l = n.value;
      t.payload = function() {
        return r(l);
      }, t.callback = function() {
        fo(e, n);
      };
    }
    var i = e.stateNode;
    return i !== null && typeof i.componentDidCatch == "function" && (t.callback = function() {
      fo(e, n), typeof r != "function" && (Gn === null ? Gn = /* @__PURE__ */ new Set([this]) : Gn.add(this));
      var s = n.stack;
      this.componentDidCatch(n.value, { componentStack: s !== null ? s : "" });
    }), t;
  }
  function na(e, n, t) {
    var r = e.pingCache;
    if (r === null) {
      r = e.pingCache = new Vd();
      var l = /* @__PURE__ */ new Set();
      r.set(n, l);
    } else l = r.get(n), l === void 0 && (l = /* @__PURE__ */ new Set(), r.set(n, l));
    l.has(t) || (l.add(t), e = _d.bind(null, e, n, t), n.then(e, e));
  }
  function ta(e) {
    do {
      var n;
      if ((n = e.tag === 13) && (n = e.memoizedState, n = n !== null ? n.dehydrated !== null : !0), n) return e;
      e = e.return;
    } while (e !== null);
    return null;
  }
  function ra(e, n, t, r, l) {
    return (e.mode & 1) === 0 ? (e === n ? e.flags |= 65536 : (e.flags |= 128, t.flags |= 131072, t.flags &= -52805, t.tag === 1 && (t.alternate === null ? t.tag = 17 : (n = On(-1, 1), n.tag = 2, Kn(t, n, 1))), t.lanes |= 1), e) : (e.flags |= 65536, e.lanes = l, e);
  }
  var Ud = fe.ReactCurrentOwner, be = !1;
  function Ke(e, n, t, r) {
    n.child = e === null ? ju(n, null, t, r) : Tt(n, e.child, t, r);
  }
  function la(e, n, t, r, l) {
    t = t.render;
    var i = n.ref;
    return Ot(n, l), r = to(e, n, t, r, i, l), t = ro(), e !== null && !be ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Fn(e, n, l)) : (me && t && Ui(n), n.flags |= 1, Ke(e, n, r, l), n.child);
  }
  function ia(e, n, t, r, l) {
    if (e === null) {
      var i = t.type;
      return typeof i == "function" && !Mo(i) && i.defaultProps === void 0 && t.compare === null && t.defaultProps === void 0 ? (n.tag = 15, n.type = i, oa(e, n, i, r, l)) : (e = Ll(t.type, null, r, n, n.mode, l), e.ref = n.ref, e.return = n, n.child = e);
    }
    if (i = e.child, (e.lanes & l) === 0) {
      var s = i.memoizedProps;
      if (t = t.compare, t = t !== null ? t : rr, t(s, r) && e.ref === n.ref) return Fn(e, n, l);
    }
    return n.flags |= 1, e = $n(i, r), e.ref = n.ref, e.return = n, n.child = e;
  }
  function oa(e, n, t, r, l) {
    if (e !== null) {
      var i = e.memoizedProps;
      if (rr(i, r) && e.ref === n.ref) if (be = !1, n.pendingProps = r = i, (e.lanes & l) !== 0) (e.flags & 131072) !== 0 && (be = !0);
      else return n.lanes = e.lanes, Fn(e, n, l);
    }
    return po(e, n, t, r, l);
  }
  function sa(e, n, t) {
    var r = n.pendingProps, l = r.children, i = e !== null ? e.memoizedState : null;
    if (r.mode === "hidden") if ((n.mode & 1) === 0) n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, se(Wt, sn), sn |= t;
    else {
      if ((t & 1073741824) === 0) return e = i !== null ? i.baseLanes | t : t, n.lanes = n.childLanes = 1073741824, n.memoizedState = { baseLanes: e, cachePool: null, transitions: null }, n.updateQueue = null, se(Wt, sn), sn |= e, null;
      n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, r = i !== null ? i.baseLanes : t, se(Wt, sn), sn |= r;
    }
    else i !== null ? (r = i.baseLanes | t, n.memoizedState = null) : r = t, se(Wt, sn), sn |= r;
    return Ke(e, n, l, t), n.child;
  }
  function ua(e, n) {
    var t = n.ref;
    (e === null && t !== null || e !== null && e.ref !== t) && (n.flags |= 512, n.flags |= 2097152);
  }
  function po(e, n, t, r, l) {
    var i = Ye(t) ? rt : qe.current;
    return i = Et(n, i), Ot(n, l), t = to(e, n, t, r, i, l), r = ro(), e !== null && !be ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Fn(e, n, l)) : (me && r && Ui(n), n.flags |= 1, Ke(e, n, t, l), n.child);
  }
  function aa(e, n, t, r, l) {
    if (Ye(t)) {
      var i = !0;
      tl(n);
    } else i = !1;
    if (Ot(n, l), n.stateNode === null) wl(e, n), bu(n, t, r), ao(n, t, r, l), r = !0;
    else if (e === null) {
      var s = n.stateNode, d = n.memoizedProps;
      s.props = d;
      var f = s.context, y = t.contextType;
      typeof y == "object" && y !== null ? y = cn(y) : (y = Ye(t) ? rt : qe.current, y = Et(n, y));
      var N = t.getDerivedStateFromProps, C = typeof N == "function" || typeof s.getSnapshotBeforeUpdate == "function";
      C || typeof s.UNSAFE_componentWillReceiveProps != "function" && typeof s.componentWillReceiveProps != "function" || (d !== r || f !== y) && _u(n, s, r, y), Jn = !1;
      var j = n.memoizedState;
      s.state = j, dl(n, r, s, l), f = n.memoizedState, d !== r || j !== f || Ge.current || Jn ? (typeof N == "function" && (uo(n, t, N, r), f = n.memoizedState), (d = Jn || Yu(n, t, d, r, j, f, y)) ? (C || typeof s.UNSAFE_componentWillMount != "function" && typeof s.componentWillMount != "function" || (typeof s.componentWillMount == "function" && s.componentWillMount(), typeof s.UNSAFE_componentWillMount == "function" && s.UNSAFE_componentWillMount()), typeof s.componentDidMount == "function" && (n.flags |= 4194308)) : (typeof s.componentDidMount == "function" && (n.flags |= 4194308), n.memoizedProps = r, n.memoizedState = f), s.props = r, s.state = f, s.context = y, r = d) : (typeof s.componentDidMount == "function" && (n.flags |= 4194308), r = !1);
    } else {
      s = n.stateNode, Cu(e, n), d = n.memoizedProps, y = n.type === n.elementType ? d : gn(n.type, d), s.props = y, C = n.pendingProps, j = s.context, f = t.contextType, typeof f == "object" && f !== null ? f = cn(f) : (f = Ye(t) ? rt : qe.current, f = Et(n, f));
      var F = t.getDerivedStateFromProps;
      (N = typeof F == "function" || typeof s.getSnapshotBeforeUpdate == "function") || typeof s.UNSAFE_componentWillReceiveProps != "function" && typeof s.componentWillReceiveProps != "function" || (d !== C || j !== f) && _u(n, s, r, f), Jn = !1, j = n.memoizedState, s.state = j, dl(n, r, s, l);
      var I = n.memoizedState;
      d !== C || j !== I || Ge.current || Jn ? (typeof F == "function" && (uo(n, t, F, r), I = n.memoizedState), (y = Jn || Yu(n, t, y, r, j, I, f) || !1) ? (N || typeof s.UNSAFE_componentWillUpdate != "function" && typeof s.componentWillUpdate != "function" || (typeof s.componentWillUpdate == "function" && s.componentWillUpdate(r, I, f), typeof s.UNSAFE_componentWillUpdate == "function" && s.UNSAFE_componentWillUpdate(r, I, f)), typeof s.componentDidUpdate == "function" && (n.flags |= 4), typeof s.getSnapshotBeforeUpdate == "function" && (n.flags |= 1024)) : (typeof s.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof s.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), n.memoizedProps = r, n.memoizedState = I), s.props = r, s.state = I, s.context = f, r = y) : (typeof s.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof s.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), r = !1);
    }
    return ho(e, n, t, r, i, l);
  }
  function ho(e, n, t, r, l, i) {
    ua(e, n);
    var s = (n.flags & 128) !== 0;
    if (!r && !s) return l && hu(n, t, !1), Fn(e, n, i);
    r = n.stateNode, Ud.current = n;
    var d = s && typeof t.getDerivedStateFromError != "function" ? null : r.render();
    return n.flags |= 1, e !== null && s ? (n.child = Tt(n, e.child, null, i), n.child = Tt(n, null, d, i)) : Ke(e, n, d, i), n.memoizedState = r.state, l && hu(n, t, !0), n.child;
  }
  function ca(e) {
    var n = e.stateNode;
    n.pendingContext ? fu(e, n.pendingContext, n.pendingContext !== n.context) : n.context && fu(e, n.context, !1), Yi(e, n.containerInfo);
  }
  function da(e, n, t, r, l) {
    return Pt(), Bi(l), n.flags |= 256, Ke(e, n, t, r), n.child;
  }
  var mo = { dehydrated: null, treeContext: null, retryLane: 0 };
  function vo(e) {
    return { baseLanes: e, cachePool: null, transitions: null };
  }
  function fa(e, n, t) {
    var r = n.pendingProps, l = ye.current, i = !1, s = (n.flags & 128) !== 0, d;
    if ((d = s) || (d = e !== null && e.memoizedState === null ? !1 : (l & 2) !== 0), d ? (i = !0, n.flags &= -129) : (e === null || e.memoizedState !== null) && (l |= 1), se(ye, l & 1), e === null)
      return Ai(n), e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? ((n.mode & 1) === 0 ? n.lanes = 1 : e.data === "$!" ? n.lanes = 8 : n.lanes = 1073741824, null) : (s = r.children, e = r.fallback, i ? (r = n.mode, i = n.child, s = { mode: "hidden", children: s }, (r & 1) === 0 && i !== null ? (i.childLanes = 0, i.pendingProps = s) : i = Ol(s, r, 0, null), e = pt(e, r, t, null), i.return = n, e.return = n, i.sibling = e, n.child = i, n.child.memoizedState = vo(t), n.memoizedState = mo, e) : go(n, s));
    if (l = e.memoizedState, l !== null && (d = l.dehydrated, d !== null)) return qd(e, n, s, r, d, l, t);
    if (i) {
      i = r.fallback, s = n.mode, l = e.child, d = l.sibling;
      var f = { mode: "hidden", children: r.children };
      return (s & 1) === 0 && n.child !== l ? (r = n.child, r.childLanes = 0, r.pendingProps = f, n.deletions = null) : (r = $n(l, f), r.subtreeFlags = l.subtreeFlags & 14680064), d !== null ? i = $n(d, i) : (i = pt(i, s, t, null), i.flags |= 2), i.return = n, r.return = n, r.sibling = i, n.child = r, r = i, i = n.child, s = e.child.memoizedState, s = s === null ? vo(t) : { baseLanes: s.baseLanes | t, cachePool: null, transitions: s.transitions }, i.memoizedState = s, i.childLanes = e.childLanes & ~t, n.memoizedState = mo, r;
    }
    return i = e.child, e = i.sibling, r = $n(i, { mode: "visible", children: r.children }), (n.mode & 1) === 0 && (r.lanes = t), r.return = n, r.sibling = null, e !== null && (t = n.deletions, t === null ? (n.deletions = [e], n.flags |= 16) : t.push(e)), n.child = r, n.memoizedState = null, r;
  }
  function go(e, n) {
    return n = Ol({ mode: "visible", children: n }, e.mode, 0, null), n.return = e, e.child = n;
  }
  function xl(e, n, t, r) {
    return r !== null && Bi(r), Tt(n, e.child, null, t), e = go(n, n.pendingProps.children), e.flags |= 2, n.memoizedState = null, e;
  }
  function qd(e, n, t, r, l, i, s) {
    if (t)
      return n.flags & 256 ? (n.flags &= -257, r = co(Error(c(422))), xl(e, n, s, r)) : n.memoizedState !== null ? (n.child = e.child, n.flags |= 128, null) : (i = r.fallback, l = n.mode, r = Ol({ mode: "visible", children: r.children }, l, 0, null), i = pt(i, l, s, null), i.flags |= 2, r.return = n, i.return = n, r.sibling = i, n.child = r, (n.mode & 1) !== 0 && Tt(n, e.child, null, s), n.child.memoizedState = vo(s), n.memoizedState = mo, i);
    if ((n.mode & 1) === 0) return xl(e, n, s, null);
    if (l.data === "$!") {
      if (r = l.nextSibling && l.nextSibling.dataset, r) var d = r.dgst;
      return r = d, i = Error(c(419)), r = co(i, r, void 0), xl(e, n, s, r);
    }
    if (d = (s & e.childLanes) !== 0, be || d) {
      if (r = Fe, r !== null) {
        switch (s & -s) {
          case 4:
            l = 2;
            break;
          case 16:
            l = 8;
            break;
          case 64:
          case 128:
          case 256:
          case 512:
          case 1024:
          case 2048:
          case 4096:
          case 8192:
          case 16384:
          case 32768:
          case 65536:
          case 131072:
          case 262144:
          case 524288:
          case 1048576:
          case 2097152:
          case 4194304:
          case 8388608:
          case 16777216:
          case 33554432:
          case 67108864:
            l = 32;
            break;
          case 536870912:
            l = 268435456;
            break;
          default:
            l = 0;
        }
        l = (l & (r.suspendedLanes | s)) !== 0 ? 0 : l, l !== 0 && l !== i.retryLane && (i.retryLane = l, Ln(e, l), wn(r, e, l, -1));
      }
      return Fo(), r = co(Error(c(421))), xl(e, n, s, r);
    }
    return l.data === "$?" ? (n.flags |= 128, n.child = e.child, n = $d.bind(null, e), l._reactRetry = n, null) : (e = i.treeContext, on = An(l.nextSibling), ln = n, me = !0, vn = null, e !== null && (un[an++] = Pn, un[an++] = Tn, un[an++] = lt, Pn = e.id, Tn = e.overflow, lt = n), n = go(n, r.children), n.flags |= 4096, n);
  }
  function pa(e, n, t) {
    e.lanes |= n;
    var r = e.alternate;
    r !== null && (r.lanes |= n), Ki(e.return, n, t);
  }
  function yo(e, n, t, r, l) {
    var i = e.memoizedState;
    i === null ? e.memoizedState = { isBackwards: n, rendering: null, renderingStartTime: 0, last: r, tail: t, tailMode: l } : (i.isBackwards = n, i.rendering = null, i.renderingStartTime = 0, i.last = r, i.tail = t, i.tailMode = l);
  }
  function ha(e, n, t) {
    var r = n.pendingProps, l = r.revealOrder, i = r.tail;
    if (Ke(e, n, r.children, t), r = ye.current, (r & 2) !== 0) r = r & 1 | 2, n.flags |= 128;
    else {
      if (e !== null && (e.flags & 128) !== 0) e: for (e = n.child; e !== null; ) {
        if (e.tag === 13) e.memoizedState !== null && pa(e, t, n);
        else if (e.tag === 19) pa(e, t, n);
        else if (e.child !== null) {
          e.child.return = e, e = e.child;
          continue;
        }
        if (e === n) break e;
        for (; e.sibling === null; ) {
          if (e.return === null || e.return === n) break e;
          e = e.return;
        }
        e.sibling.return = e.return, e = e.sibling;
      }
      r &= 1;
    }
    if (se(ye, r), (n.mode & 1) === 0) n.memoizedState = null;
    else switch (l) {
      case "forwards":
        for (t = n.child, l = null; t !== null; ) e = t.alternate, e !== null && fl(e) === null && (l = t), t = t.sibling;
        t = l, t === null ? (l = n.child, n.child = null) : (l = t.sibling, t.sibling = null), yo(n, !1, l, t, i);
        break;
      case "backwards":
        for (t = null, l = n.child, n.child = null; l !== null; ) {
          if (e = l.alternate, e !== null && fl(e) === null) {
            n.child = l;
            break;
          }
          e = l.sibling, l.sibling = t, t = l, l = e;
        }
        yo(n, !0, t, null, i);
        break;
      case "together":
        yo(n, !1, null, null, void 0);
        break;
      default:
        n.memoizedState = null;
    }
    return n.child;
  }
  function wl(e, n) {
    (n.mode & 1) === 0 && e !== null && (e.alternate = null, n.alternate = null, n.flags |= 2);
  }
  function Fn(e, n, t) {
    if (e !== null && (n.dependencies = e.dependencies), at |= n.lanes, (t & n.childLanes) === 0) return null;
    if (e !== null && n.child !== e.child) throw Error(c(153));
    if (n.child !== null) {
      for (e = n.child, t = $n(e, e.pendingProps), n.child = t, t.return = n; e.sibling !== null; ) e = e.sibling, t = t.sibling = $n(e, e.pendingProps), t.return = n;
      t.sibling = null;
    }
    return n.child;
  }
  function Hd(e, n, t) {
    switch (n.tag) {
      case 3:
        ca(n), Pt();
        break;
      case 5:
        Ru(n);
        break;
      case 1:
        Ye(n.type) && tl(n);
        break;
      case 4:
        Yi(n, n.stateNode.containerInfo);
        break;
      case 10:
        var r = n.type._context, l = n.memoizedProps.value;
        se(ul, r._currentValue), r._currentValue = l;
        break;
      case 13:
        if (r = n.memoizedState, r !== null)
          return r.dehydrated !== null ? (se(ye, ye.current & 1), n.flags |= 128, null) : (t & n.child.childLanes) !== 0 ? fa(e, n, t) : (se(ye, ye.current & 1), e = Fn(e, n, t), e !== null ? e.sibling : null);
        se(ye, ye.current & 1);
        break;
      case 19:
        if (r = (t & n.childLanes) !== 0, (e.flags & 128) !== 0) {
          if (r) return ha(e, n, t);
          n.flags |= 128;
        }
        if (l = n.memoizedState, l !== null && (l.rendering = null, l.tail = null, l.lastEffect = null), se(ye, ye.current), r) break;
        return null;
      case 22:
      case 23:
        return n.lanes = 0, sa(e, n, t);
    }
    return Fn(e, n, t);
  }
  var ma, xo, va, ga;
  ma = function(e, n) {
    for (var t = n.child; t !== null; ) {
      if (t.tag === 5 || t.tag === 6) e.appendChild(t.stateNode);
      else if (t.tag !== 4 && t.child !== null) {
        t.child.return = t, t = t.child;
        continue;
      }
      if (t === n) break;
      for (; t.sibling === null; ) {
        if (t.return === null || t.return === n) return;
        t = t.return;
      }
      t.sibling.return = t.return, t = t.sibling;
    }
  }, xo = function() {
  }, va = function(e, n, t, r) {
    var l = e.memoizedProps;
    if (l !== r) {
      e = n.stateNode, st(Nn.current);
      var i = null;
      switch (t) {
        case "input":
          l = Kl(e, l), r = Kl(e, r), i = [];
          break;
        case "select":
          l = P({}, l, { value: void 0 }), r = P({}, r, { value: void 0 }), i = [];
          break;
        case "textarea":
          l = Yl(e, l), r = Yl(e, r), i = [];
          break;
        default:
          typeof l.onClick != "function" && typeof r.onClick == "function" && (e.onclick = $r);
      }
      _l(t, r);
      var s;
      t = null;
      for (y in l) if (!r.hasOwnProperty(y) && l.hasOwnProperty(y) && l[y] != null) if (y === "style") {
        var d = l[y];
        for (s in d) d.hasOwnProperty(s) && (t || (t = {}), t[s] = "");
      } else y !== "dangerouslySetInnerHTML" && y !== "children" && y !== "suppressContentEditableWarning" && y !== "suppressHydrationWarning" && y !== "autoFocus" && (w.hasOwnProperty(y) ? i || (i = []) : (i = i || []).push(y, null));
      for (y in r) {
        var f = r[y];
        if (d = l != null ? l[y] : void 0, r.hasOwnProperty(y) && f !== d && (f != null || d != null)) if (y === "style") if (d) {
          for (s in d) !d.hasOwnProperty(s) || f && f.hasOwnProperty(s) || (t || (t = {}), t[s] = "");
          for (s in f) f.hasOwnProperty(s) && d[s] !== f[s] && (t || (t = {}), t[s] = f[s]);
        } else t || (i || (i = []), i.push(
          y,
          t
        )), t = f;
        else y === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, d = d ? d.__html : void 0, f != null && d !== f && (i = i || []).push(y, f)) : y === "children" ? typeof f != "string" && typeof f != "number" || (i = i || []).push(y, "" + f) : y !== "suppressContentEditableWarning" && y !== "suppressHydrationWarning" && (w.hasOwnProperty(y) ? (f != null && y === "onScroll" && ce("scroll", e), i || d === f || (i = [])) : (i = i || []).push(y, f));
      }
      t && (i = i || []).push("style", t);
      var y = i;
      (n.updateQueue = y) && (n.flags |= 4);
    }
  }, ga = function(e, n, t, r) {
    t !== r && (n.flags |= 4);
  };
  function yr(e, n) {
    if (!me) switch (e.tailMode) {
      case "hidden":
        n = e.tail;
        for (var t = null; n !== null; ) n.alternate !== null && (t = n), n = n.sibling;
        t === null ? e.tail = null : t.sibling = null;
        break;
      case "collapsed":
        t = e.tail;
        for (var r = null; t !== null; ) t.alternate !== null && (r = t), t = t.sibling;
        r === null ? n || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
    }
  }
  function Ae(e) {
    var n = e.alternate !== null && e.alternate.child === e.child, t = 0, r = 0;
    if (n) for (var l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags & 14680064, r |= l.flags & 14680064, l.return = e, l = l.sibling;
    else for (l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags, r |= l.flags, l.return = e, l = l.sibling;
    return e.subtreeFlags |= r, e.childLanes = t, n;
  }
  function Ad(e, n, t) {
    var r = n.pendingProps;
    switch (qi(n), n.tag) {
      case 2:
      case 16:
      case 15:
      case 0:
      case 11:
      case 7:
      case 8:
      case 12:
      case 9:
      case 14:
        return Ae(n), null;
      case 1:
        return Ye(n.type) && nl(), Ae(n), null;
      case 3:
        return r = n.stateNode, Ft(), de(Ge), de(qe), $i(), r.pendingContext && (r.context = r.pendingContext, r.pendingContext = null), (e === null || e.child === null) && (ol(n) ? n.flags |= 4 : e === null || e.memoizedState.isDehydrated && (n.flags & 256) === 0 || (n.flags |= 1024, vn !== null && (To(vn), vn = null))), xo(e, n), Ae(n), null;
      case 5:
        bi(n);
        var l = st(pr.current);
        if (t = n.type, e !== null && n.stateNode != null) va(e, n, t, r, l), e.ref !== n.ref && (n.flags |= 512, n.flags |= 2097152);
        else {
          if (!r) {
            if (n.stateNode === null) throw Error(c(166));
            return Ae(n), null;
          }
          if (e = st(Nn.current), ol(n)) {
            r = n.stateNode, t = n.type;
            var i = n.memoizedProps;
            switch (r[jn] = n, r[ur] = i, e = (n.mode & 1) !== 0, t) {
              case "dialog":
                ce("cancel", r), ce("close", r);
                break;
              case "iframe":
              case "object":
              case "embed":
                ce("load", r);
                break;
              case "video":
              case "audio":
                for (l = 0; l < ir.length; l++) ce(ir[l], r);
                break;
              case "source":
                ce("error", r);
                break;
              case "img":
              case "image":
              case "link":
                ce(
                  "error",
                  r
                ), ce("load", r);
                break;
              case "details":
                ce("toggle", r);
                break;
              case "input":
                bo(r, i), ce("invalid", r);
                break;
              case "select":
                r._wrapperState = { wasMultiple: !!i.multiple }, ce("invalid", r);
                break;
              case "textarea":
                es(r, i), ce("invalid", r);
            }
            _l(t, i), l = null;
            for (var s in i) if (i.hasOwnProperty(s)) {
              var d = i[s];
              s === "children" ? typeof d == "string" ? r.textContent !== d && (i.suppressHydrationWarning !== !0 && _r(r.textContent, d, e), l = ["children", d]) : typeof d == "number" && r.textContent !== "" + d && (i.suppressHydrationWarning !== !0 && _r(
                r.textContent,
                d,
                e
              ), l = ["children", "" + d]) : w.hasOwnProperty(s) && d != null && s === "onScroll" && ce("scroll", r);
            }
            switch (t) {
              case "input":
                Pr(r), $o(r, i, !0);
                break;
              case "textarea":
                Pr(r), ts(r);
                break;
              case "select":
              case "option":
                break;
              default:
                typeof i.onClick == "function" && (r.onclick = $r);
            }
            r = l, n.updateQueue = r, r !== null && (n.flags |= 4);
          } else {
            s = l.nodeType === 9 ? l : l.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = rs(t)), e === "http://www.w3.org/1999/xhtml" ? t === "script" ? (e = s.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof r.is == "string" ? e = s.createElement(t, { is: r.is }) : (e = s.createElement(t), t === "select" && (s = e, r.multiple ? s.multiple = !0 : r.size && (s.size = r.size))) : e = s.createElementNS(e, t), e[jn] = n, e[ur] = r, ma(e, n, !1, !1), n.stateNode = e;
            e: {
              switch (s = $l(t, r), t) {
                case "dialog":
                  ce("cancel", e), ce("close", e), l = r;
                  break;
                case "iframe":
                case "object":
                case "embed":
                  ce("load", e), l = r;
                  break;
                case "video":
                case "audio":
                  for (l = 0; l < ir.length; l++) ce(ir[l], e);
                  l = r;
                  break;
                case "source":
                  ce("error", e), l = r;
                  break;
                case "img":
                case "image":
                case "link":
                  ce(
                    "error",
                    e
                  ), ce("load", e), l = r;
                  break;
                case "details":
                  ce("toggle", e), l = r;
                  break;
                case "input":
                  bo(e, r), l = Kl(e, r), ce("invalid", e);
                  break;
                case "option":
                  l = r;
                  break;
                case "select":
                  e._wrapperState = { wasMultiple: !!r.multiple }, l = P({}, r, { value: void 0 }), ce("invalid", e);
                  break;
                case "textarea":
                  es(e, r), l = Yl(e, r), ce("invalid", e);
                  break;
                default:
                  l = r;
              }
              _l(t, l), d = l;
              for (i in d) if (d.hasOwnProperty(i)) {
                var f = d[i];
                i === "style" ? os(e, f) : i === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, f != null && ls(e, f)) : i === "children" ? typeof f == "string" ? (t !== "textarea" || f !== "") && qt(e, f) : typeof f == "number" && qt(e, "" + f) : i !== "suppressContentEditableWarning" && i !== "suppressHydrationWarning" && i !== "autoFocus" && (w.hasOwnProperty(i) ? f != null && i === "onScroll" && ce("scroll", e) : f != null && ge(e, i, f, s));
              }
              switch (t) {
                case "input":
                  Pr(e), $o(e, r, !1);
                  break;
                case "textarea":
                  Pr(e), ts(e);
                  break;
                case "option":
                  r.value != null && e.setAttribute("value", "" + re(r.value));
                  break;
                case "select":
                  e.multiple = !!r.multiple, i = r.value, i != null ? ht(e, !!r.multiple, i, !1) : r.defaultValue != null && ht(
                    e,
                    !!r.multiple,
                    r.defaultValue,
                    !0
                  );
                  break;
                default:
                  typeof l.onClick == "function" && (e.onclick = $r);
              }
              switch (t) {
                case "button":
                case "input":
                case "select":
                case "textarea":
                  r = !!r.autoFocus;
                  break e;
                case "img":
                  r = !0;
                  break e;
                default:
                  r = !1;
              }
            }
            r && (n.flags |= 4);
          }
          n.ref !== null && (n.flags |= 512, n.flags |= 2097152);
        }
        return Ae(n), null;
      case 6:
        if (e && n.stateNode != null) ga(e, n, e.memoizedProps, r);
        else {
          if (typeof r != "string" && n.stateNode === null) throw Error(c(166));
          if (t = st(pr.current), st(Nn.current), ol(n)) {
            if (r = n.stateNode, t = n.memoizedProps, r[jn] = n, (i = r.nodeValue !== t) && (e = ln, e !== null)) switch (e.tag) {
              case 3:
                _r(r.nodeValue, t, (e.mode & 1) !== 0);
                break;
              case 5:
                e.memoizedProps.suppressHydrationWarning !== !0 && _r(r.nodeValue, t, (e.mode & 1) !== 0);
            }
            i && (n.flags |= 4);
          } else r = (t.nodeType === 9 ? t : t.ownerDocument).createTextNode(r), r[jn] = n, n.stateNode = r;
        }
        return Ae(n), null;
      case 13:
        if (de(ye), r = n.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
          if (me && on !== null && (n.mode & 1) !== 0 && (n.flags & 128) === 0) wu(), Pt(), n.flags |= 98560, i = !1;
          else if (i = ol(n), r !== null && r.dehydrated !== null) {
            if (e === null) {
              if (!i) throw Error(c(318));
              if (i = n.memoizedState, i = i !== null ? i.dehydrated : null, !i) throw Error(c(317));
              i[jn] = n;
            } else Pt(), (n.flags & 128) === 0 && (n.memoizedState = null), n.flags |= 4;
            Ae(n), i = !1;
          } else vn !== null && (To(vn), vn = null), i = !0;
          if (!i) return n.flags & 65536 ? n : null;
        }
        return (n.flags & 128) !== 0 ? (n.lanes = t, n) : (r = r !== null, r !== (e !== null && e.memoizedState !== null) && r && (n.child.flags |= 8192, (n.mode & 1) !== 0 && (e === null || (ye.current & 1) !== 0 ? Pe === 0 && (Pe = 3) : Fo())), n.updateQueue !== null && (n.flags |= 4), Ae(n), null);
      case 4:
        return Ft(), xo(e, n), e === null && or(n.stateNode.containerInfo), Ae(n), null;
      case 10:
        return Ji(n.type._context), Ae(n), null;
      case 17:
        return Ye(n.type) && nl(), Ae(n), null;
      case 19:
        if (de(ye), i = n.memoizedState, i === null) return Ae(n), null;
        if (r = (n.flags & 128) !== 0, s = i.rendering, s === null) if (r) yr(i, !1);
        else {
          if (Pe !== 0 || e !== null && (e.flags & 128) !== 0) for (e = n.child; e !== null; ) {
            if (s = fl(e), s !== null) {
              for (n.flags |= 128, yr(i, !1), r = s.updateQueue, r !== null && (n.updateQueue = r, n.flags |= 4), n.subtreeFlags = 0, r = t, t = n.child; t !== null; ) i = t, e = r, i.flags &= 14680066, s = i.alternate, s === null ? (i.childLanes = 0, i.lanes = e, i.child = null, i.subtreeFlags = 0, i.memoizedProps = null, i.memoizedState = null, i.updateQueue = null, i.dependencies = null, i.stateNode = null) : (i.childLanes = s.childLanes, i.lanes = s.lanes, i.child = s.child, i.subtreeFlags = 0, i.deletions = null, i.memoizedProps = s.memoizedProps, i.memoizedState = s.memoizedState, i.updateQueue = s.updateQueue, i.type = s.type, e = s.dependencies, i.dependencies = e === null ? null : { lanes: e.lanes, firstContext: e.firstContext }), t = t.sibling;
              return se(ye, ye.current & 1 | 2), n.child;
            }
            e = e.sibling;
          }
          i.tail !== null && Se() > Dt && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
        }
        else {
          if (!r) if (e = fl(s), e !== null) {
            if (n.flags |= 128, r = !0, t = e.updateQueue, t !== null && (n.updateQueue = t, n.flags |= 4), yr(i, !0), i.tail === null && i.tailMode === "hidden" && !s.alternate && !me) return Ae(n), null;
          } else 2 * Se() - i.renderingStartTime > Dt && t !== 1073741824 && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
          i.isBackwards ? (s.sibling = n.child, n.child = s) : (t = i.last, t !== null ? t.sibling = s : n.child = s, i.last = s);
        }
        return i.tail !== null ? (n = i.tail, i.rendering = n, i.tail = n.sibling, i.renderingStartTime = Se(), n.sibling = null, t = ye.current, se(ye, r ? t & 1 | 2 : t & 1), n) : (Ae(n), null);
      case 22:
      case 23:
        return Oo(), r = n.memoizedState !== null, e !== null && e.memoizedState !== null !== r && (n.flags |= 8192), r && (n.mode & 1) !== 0 ? (sn & 1073741824) !== 0 && (Ae(n), n.subtreeFlags & 6 && (n.flags |= 8192)) : Ae(n), null;
      case 24:
        return null;
      case 25:
        return null;
    }
    throw Error(c(156, n.tag));
  }
  function Bd(e, n) {
    switch (qi(n), n.tag) {
      case 1:
        return Ye(n.type) && nl(), e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 3:
        return Ft(), de(Ge), de(qe), $i(), e = n.flags, (e & 65536) !== 0 && (e & 128) === 0 ? (n.flags = e & -65537 | 128, n) : null;
      case 5:
        return bi(n), null;
      case 13:
        if (de(ye), e = n.memoizedState, e !== null && e.dehydrated !== null) {
          if (n.alternate === null) throw Error(c(340));
          Pt();
        }
        return e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 19:
        return de(ye), null;
      case 4:
        return Ft(), null;
      case 10:
        return Ji(n.type._context), null;
      case 22:
      case 23:
        return Oo(), null;
      case 24:
        return null;
      default:
        return null;
    }
  }
  var kl = !1, Be = !1, Xd = typeof WeakSet == "function" ? WeakSet : Set, M = null;
  function It(e, n) {
    var t = e.ref;
    if (t !== null) if (typeof t == "function") try {
      t(null);
    } catch (r) {
      we(e, n, r);
    }
    else t.current = null;
  }
  function wo(e, n, t) {
    try {
      t();
    } catch (r) {
      we(e, n, r);
    }
  }
  var ya = !1;
  function Zd(e, n) {
    if (Li = Hr, e = Ys(), ji(e)) {
      if ("selectionStart" in e) var t = { start: e.selectionStart, end: e.selectionEnd };
      else e: {
        t = (t = e.ownerDocument) && t.defaultView || window;
        var r = t.getSelection && t.getSelection();
        if (r && r.rangeCount !== 0) {
          t = r.anchorNode;
          var l = r.anchorOffset, i = r.focusNode;
          r = r.focusOffset;
          try {
            t.nodeType, i.nodeType;
          } catch {
            t = null;
            break e;
          }
          var s = 0, d = -1, f = -1, y = 0, N = 0, C = e, j = null;
          n: for (; ; ) {
            for (var F; C !== t || l !== 0 && C.nodeType !== 3 || (d = s + l), C !== i || r !== 0 && C.nodeType !== 3 || (f = s + r), C.nodeType === 3 && (s += C.nodeValue.length), (F = C.firstChild) !== null; )
              j = C, C = F;
            for (; ; ) {
              if (C === e) break n;
              if (j === t && ++y === l && (d = s), j === i && ++N === r && (f = s), (F = C.nextSibling) !== null) break;
              C = j, j = C.parentNode;
            }
            C = F;
          }
          t = d === -1 || f === -1 ? null : { start: d, end: f };
        } else t = null;
      }
      t = t || { start: 0, end: 0 };
    } else t = null;
    for (Oi = { focusedElem: e, selectionRange: t }, Hr = !1, M = n; M !== null; ) if (n = M, e = n.child, (n.subtreeFlags & 1028) !== 0 && e !== null) e.return = n, M = e;
    else for (; M !== null; ) {
      n = M;
      try {
        var I = n.alternate;
        if ((n.flags & 1024) !== 0) switch (n.tag) {
          case 0:
          case 11:
          case 15:
            break;
          case 1:
            if (I !== null) {
              var W = I.memoizedProps, je = I.memoizedState, m = n.stateNode, p = m.getSnapshotBeforeUpdate(n.elementType === n.type ? W : gn(n.type, W), je);
              m.__reactInternalSnapshotBeforeUpdate = p;
            }
            break;
          case 3:
            var v = n.stateNode.containerInfo;
            v.nodeType === 1 ? v.textContent = "" : v.nodeType === 9 && v.documentElement && v.removeChild(v.documentElement);
            break;
          case 5:
          case 6:
          case 4:
          case 17:
            break;
          default:
            throw Error(c(163));
        }
      } catch (R) {
        we(n, n.return, R);
      }
      if (e = n.sibling, e !== null) {
        e.return = n.return, M = e;
        break;
      }
      M = n.return;
    }
    return I = ya, ya = !1, I;
  }
  function xr(e, n, t) {
    var r = n.updateQueue;
    if (r = r !== null ? r.lastEffect : null, r !== null) {
      var l = r = r.next;
      do {
        if ((l.tag & e) === e) {
          var i = l.destroy;
          l.destroy = void 0, i !== void 0 && wo(n, t, i);
        }
        l = l.next;
      } while (l !== r);
    }
  }
  function Sl(e, n) {
    if (n = n.updateQueue, n = n !== null ? n.lastEffect : null, n !== null) {
      var t = n = n.next;
      do {
        if ((t.tag & e) === e) {
          var r = t.create;
          t.destroy = r();
        }
        t = t.next;
      } while (t !== n);
    }
  }
  function ko(e) {
    var n = e.ref;
    if (n !== null) {
      var t = e.stateNode;
      switch (e.tag) {
        case 5:
          e = t;
          break;
        default:
          e = t;
      }
      typeof n == "function" ? n(e) : n.current = e;
    }
  }
  function xa(e) {
    var n = e.alternate;
    n !== null && (e.alternate = null, xa(n)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (n = e.stateNode, n !== null && (delete n[jn], delete n[ur], delete n[Wi], delete n[zd], delete n[Rd])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
  }
  function wa(e) {
    return e.tag === 5 || e.tag === 3 || e.tag === 4;
  }
  function ka(e) {
    e: for (; ; ) {
      for (; e.sibling === null; ) {
        if (e.return === null || wa(e.return)) return null;
        e = e.return;
      }
      for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18; ) {
        if (e.flags & 2 || e.child === null || e.tag === 4) continue e;
        e.child.return = e, e = e.child;
      }
      if (!(e.flags & 2)) return e.stateNode;
    }
  }
  function So(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.nodeType === 8 ? t.parentNode.insertBefore(e, n) : t.insertBefore(e, n) : (t.nodeType === 8 ? (n = t.parentNode, n.insertBefore(e, t)) : (n = t, n.appendChild(e)), t = t._reactRootContainer, t != null || n.onclick !== null || (n.onclick = $r));
    else if (r !== 4 && (e = e.child, e !== null)) for (So(e, n, t), e = e.sibling; e !== null; ) So(e, n, t), e = e.sibling;
  }
  function jo(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.insertBefore(e, n) : t.appendChild(e);
    else if (r !== 4 && (e = e.child, e !== null)) for (jo(e, n, t), e = e.sibling; e !== null; ) jo(e, n, t), e = e.sibling;
  }
  var De = null, yn = !1;
  function Qn(e, n, t) {
    for (t = t.child; t !== null; ) Sa(e, n, t), t = t.sibling;
  }
  function Sa(e, n, t) {
    if (Sn && typeof Sn.onCommitFiberUnmount == "function") try {
      Sn.onCommitFiberUnmount(Ir, t);
    } catch {
    }
    switch (t.tag) {
      case 5:
        Be || It(t, n);
      case 6:
        var r = De, l = yn;
        De = null, Qn(e, n, t), De = r, yn = l, De !== null && (yn ? (e = De, t = t.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(t) : e.removeChild(t)) : De.removeChild(t.stateNode));
        break;
      case 18:
        De !== null && (yn ? (e = De, t = t.stateNode, e.nodeType === 8 ? Ii(e.parentNode, t) : e.nodeType === 1 && Ii(e, t), bt(e)) : Ii(De, t.stateNode));
        break;
      case 4:
        r = De, l = yn, De = t.stateNode.containerInfo, yn = !0, Qn(e, n, t), De = r, yn = l;
        break;
      case 0:
      case 11:
      case 14:
      case 15:
        if (!Be && (r = t.updateQueue, r !== null && (r = r.lastEffect, r !== null))) {
          l = r = r.next;
          do {
            var i = l, s = i.destroy;
            i = i.tag, s !== void 0 && ((i & 2) !== 0 || (i & 4) !== 0) && wo(t, n, s), l = l.next;
          } while (l !== r);
        }
        Qn(e, n, t);
        break;
      case 1:
        if (!Be && (It(t, n), r = t.stateNode, typeof r.componentWillUnmount == "function")) try {
          r.props = t.memoizedProps, r.state = t.memoizedState, r.componentWillUnmount();
        } catch (d) {
          we(t, n, d);
        }
        Qn(e, n, t);
        break;
      case 21:
        Qn(e, n, t);
        break;
      case 22:
        t.mode & 1 ? (Be = (r = Be) || t.memoizedState !== null, Qn(e, n, t), Be = r) : Qn(e, n, t);
        break;
      default:
        Qn(e, n, t);
    }
  }
  function ja(e) {
    var n = e.updateQueue;
    if (n !== null) {
      e.updateQueue = null;
      var t = e.stateNode;
      t === null && (t = e.stateNode = new Xd()), n.forEach(function(r) {
        var l = ef.bind(null, e, r);
        t.has(r) || (t.add(r), r.then(l, l));
      });
    }
  }
  function xn(e, n) {
    var t = n.deletions;
    if (t !== null) for (var r = 0; r < t.length; r++) {
      var l = t[r];
      try {
        var i = e, s = n, d = s;
        e: for (; d !== null; ) {
          switch (d.tag) {
            case 5:
              De = d.stateNode, yn = !1;
              break e;
            case 3:
              De = d.stateNode.containerInfo, yn = !0;
              break e;
            case 4:
              De = d.stateNode.containerInfo, yn = !0;
              break e;
          }
          d = d.return;
        }
        if (De === null) throw Error(c(160));
        Sa(i, s, l), De = null, yn = !1;
        var f = l.alternate;
        f !== null && (f.return = null), l.return = null;
      } catch (y) {
        we(l, n, y);
      }
    }
    if (n.subtreeFlags & 12854) for (n = n.child; n !== null; ) Na(n, e), n = n.sibling;
  }
  function Na(e, n) {
    var t = e.alternate, r = e.flags;
    switch (e.tag) {
      case 0:
      case 11:
      case 14:
      case 15:
        if (xn(n, e), En(e), r & 4) {
          try {
            xr(3, e, e.return), Sl(3, e);
          } catch (W) {
            we(e, e.return, W);
          }
          try {
            xr(5, e, e.return);
          } catch (W) {
            we(e, e.return, W);
          }
        }
        break;
      case 1:
        xn(n, e), En(e), r & 512 && t !== null && It(t, t.return);
        break;
      case 5:
        if (xn(n, e), En(e), r & 512 && t !== null && It(t, t.return), e.flags & 32) {
          var l = e.stateNode;
          try {
            qt(l, "");
          } catch (W) {
            we(e, e.return, W);
          }
        }
        if (r & 4 && (l = e.stateNode, l != null)) {
          var i = e.memoizedProps, s = t !== null ? t.memoizedProps : i, d = e.type, f = e.updateQueue;
          if (e.updateQueue = null, f !== null) try {
            d === "input" && i.type === "radio" && i.name != null && _o(l, i), $l(d, s);
            var y = $l(d, i);
            for (s = 0; s < f.length; s += 2) {
              var N = f[s], C = f[s + 1];
              N === "style" ? os(l, C) : N === "dangerouslySetInnerHTML" ? ls(l, C) : N === "children" ? qt(l, C) : ge(l, N, C, y);
            }
            switch (d) {
              case "input":
                Ql(l, i);
                break;
              case "textarea":
                ns(l, i);
                break;
              case "select":
                var j = l._wrapperState.wasMultiple;
                l._wrapperState.wasMultiple = !!i.multiple;
                var F = i.value;
                F != null ? ht(l, !!i.multiple, F, !1) : j !== !!i.multiple && (i.defaultValue != null ? ht(
                  l,
                  !!i.multiple,
                  i.defaultValue,
                  !0
                ) : ht(l, !!i.multiple, i.multiple ? [] : "", !1));
            }
            l[ur] = i;
          } catch (W) {
            we(e, e.return, W);
          }
        }
        break;
      case 6:
        if (xn(n, e), En(e), r & 4) {
          if (e.stateNode === null) throw Error(c(162));
          l = e.stateNode, i = e.memoizedProps;
          try {
            l.nodeValue = i;
          } catch (W) {
            we(e, e.return, W);
          }
        }
        break;
      case 3:
        if (xn(n, e), En(e), r & 4 && t !== null && t.memoizedState.isDehydrated) try {
          bt(n.containerInfo);
        } catch (W) {
          we(e, e.return, W);
        }
        break;
      case 4:
        xn(n, e), En(e);
        break;
      case 13:
        xn(n, e), En(e), l = e.child, l.flags & 8192 && (i = l.memoizedState !== null, l.stateNode.isHidden = i, !i || l.alternate !== null && l.alternate.memoizedState !== null || (Eo = Se())), r & 4 && ja(e);
        break;
      case 22:
        if (N = t !== null && t.memoizedState !== null, e.mode & 1 ? (Be = (y = Be) || N, xn(n, e), Be = y) : xn(n, e), En(e), r & 8192) {
          if (y = e.memoizedState !== null, (e.stateNode.isHidden = y) && !N && (e.mode & 1) !== 0) for (M = e, N = e.child; N !== null; ) {
            for (C = M = N; M !== null; ) {
              switch (j = M, F = j.child, j.tag) {
                case 0:
                case 11:
                case 14:
                case 15:
                  xr(4, j, j.return);
                  break;
                case 1:
                  It(j, j.return);
                  var I = j.stateNode;
                  if (typeof I.componentWillUnmount == "function") {
                    r = j, t = j.return;
                    try {
                      n = r, I.props = n.memoizedProps, I.state = n.memoizedState, I.componentWillUnmount();
                    } catch (W) {
                      we(r, t, W);
                    }
                  }
                  break;
                case 5:
                  It(j, j.return);
                  break;
                case 22:
                  if (j.memoizedState !== null) {
                    za(C);
                    continue;
                  }
              }
              F !== null ? (F.return = j, M = F) : za(C);
            }
            N = N.sibling;
          }
          e: for (N = null, C = e; ; ) {
            if (C.tag === 5) {
              if (N === null) {
                N = C;
                try {
                  l = C.stateNode, y ? (i = l.style, typeof i.setProperty == "function" ? i.setProperty("display", "none", "important") : i.display = "none") : (d = C.stateNode, f = C.memoizedProps.style, s = f != null && f.hasOwnProperty("display") ? f.display : null, d.style.display = is("display", s));
                } catch (W) {
                  we(e, e.return, W);
                }
              }
            } else if (C.tag === 6) {
              if (N === null) try {
                C.stateNode.nodeValue = y ? "" : C.memoizedProps;
              } catch (W) {
                we(e, e.return, W);
              }
            } else if ((C.tag !== 22 && C.tag !== 23 || C.memoizedState === null || C === e) && C.child !== null) {
              C.child.return = C, C = C.child;
              continue;
            }
            if (C === e) break e;
            for (; C.sibling === null; ) {
              if (C.return === null || C.return === e) break e;
              N === C && (N = null), C = C.return;
            }
            N === C && (N = null), C.sibling.return = C.return, C = C.sibling;
          }
        }
        break;
      case 19:
        xn(n, e), En(e), r & 4 && ja(e);
        break;
      case 21:
        break;
      default:
        xn(
          n,
          e
        ), En(e);
    }
  }
  function En(e) {
    var n = e.flags;
    if (n & 2) {
      try {
        e: {
          for (var t = e.return; t !== null; ) {
            if (wa(t)) {
              var r = t;
              break e;
            }
            t = t.return;
          }
          throw Error(c(160));
        }
        switch (r.tag) {
          case 5:
            var l = r.stateNode;
            r.flags & 32 && (qt(l, ""), r.flags &= -33);
            var i = ka(e);
            jo(e, i, l);
            break;
          case 3:
          case 4:
            var s = r.stateNode.containerInfo, d = ka(e);
            So(e, d, s);
            break;
          default:
            throw Error(c(161));
        }
      } catch (f) {
        we(e, e.return, f);
      }
      e.flags &= -3;
    }
    n & 4096 && (e.flags &= -4097);
  }
  function Jd(e, n, t) {
    M = e, Ca(e);
  }
  function Ca(e, n, t) {
    for (var r = (e.mode & 1) !== 0; M !== null; ) {
      var l = M, i = l.child;
      if (l.tag === 22 && r) {
        var s = l.memoizedState !== null || kl;
        if (!s) {
          var d = l.alternate, f = d !== null && d.memoizedState !== null || Be;
          d = kl;
          var y = Be;
          if (kl = s, (Be = f) && !y) for (M = l; M !== null; ) s = M, f = s.child, s.tag === 22 && s.memoizedState !== null ? Ra(l) : f !== null ? (f.return = s, M = f) : Ra(l);
          for (; i !== null; ) M = i, Ca(i), i = i.sibling;
          M = l, kl = d, Be = y;
        }
        Ea(e);
      } else (l.subtreeFlags & 8772) !== 0 && i !== null ? (i.return = l, M = i) : Ea(e);
    }
  }
  function Ea(e) {
    for (; M !== null; ) {
      var n = M;
      if ((n.flags & 8772) !== 0) {
        var t = n.alternate;
        try {
          if ((n.flags & 8772) !== 0) switch (n.tag) {
            case 0:
            case 11:
            case 15:
              Be || Sl(5, n);
              break;
            case 1:
              var r = n.stateNode;
              if (n.flags & 4 && !Be) if (t === null) r.componentDidMount();
              else {
                var l = n.elementType === n.type ? t.memoizedProps : gn(n.type, t.memoizedProps);
                r.componentDidUpdate(l, t.memoizedState, r.__reactInternalSnapshotBeforeUpdate);
              }
              var i = n.updateQueue;
              i !== null && zu(n, i, r);
              break;
            case 3:
              var s = n.updateQueue;
              if (s !== null) {
                if (t = null, n.child !== null) switch (n.child.tag) {
                  case 5:
                    t = n.child.stateNode;
                    break;
                  case 1:
                    t = n.child.stateNode;
                }
                zu(n, s, t);
              }
              break;
            case 5:
              var d = n.stateNode;
              if (t === null && n.flags & 4) {
                t = d;
                var f = n.memoizedProps;
                switch (n.type) {
                  case "button":
                  case "input":
                  case "select":
                  case "textarea":
                    f.autoFocus && t.focus();
                    break;
                  case "img":
                    f.src && (t.src = f.src);
                }
              }
              break;
            case 6:
              break;
            case 4:
              break;
            case 12:
              break;
            case 13:
              if (n.memoizedState === null) {
                var y = n.alternate;
                if (y !== null) {
                  var N = y.memoizedState;
                  if (N !== null) {
                    var C = N.dehydrated;
                    C !== null && bt(C);
                  }
                }
              }
              break;
            case 19:
            case 17:
            case 21:
            case 22:
            case 23:
            case 25:
              break;
            default:
              throw Error(c(163));
          }
          Be || n.flags & 512 && ko(n);
        } catch (j) {
          we(n, n.return, j);
        }
      }
      if (n === e) {
        M = null;
        break;
      }
      if (t = n.sibling, t !== null) {
        t.return = n.return, M = t;
        break;
      }
      M = n.return;
    }
  }
  function za(e) {
    for (; M !== null; ) {
      var n = M;
      if (n === e) {
        M = null;
        break;
      }
      var t = n.sibling;
      if (t !== null) {
        t.return = n.return, M = t;
        break;
      }
      M = n.return;
    }
  }
  function Ra(e) {
    for (; M !== null; ) {
      var n = M;
      try {
        switch (n.tag) {
          case 0:
          case 11:
          case 15:
            var t = n.return;
            try {
              Sl(4, n);
            } catch (f) {
              we(n, t, f);
            }
            break;
          case 1:
            var r = n.stateNode;
            if (typeof r.componentDidMount == "function") {
              var l = n.return;
              try {
                r.componentDidMount();
              } catch (f) {
                we(n, l, f);
              }
            }
            var i = n.return;
            try {
              ko(n);
            } catch (f) {
              we(n, i, f);
            }
            break;
          case 5:
            var s = n.return;
            try {
              ko(n);
            } catch (f) {
              we(n, s, f);
            }
        }
      } catch (f) {
        we(n, n.return, f);
      }
      if (n === e) {
        M = null;
        break;
      }
      var d = n.sibling;
      if (d !== null) {
        d.return = n.return, M = d;
        break;
      }
      M = n.return;
    }
  }
  var Kd = Math.ceil, jl = fe.ReactCurrentDispatcher, No = fe.ReactCurrentOwner, fn = fe.ReactCurrentBatchConfig, $ = 0, Fe = null, Ee = null, Ve = 0, sn = 0, Wt = Bn(0), Pe = 0, wr = null, at = 0, Nl = 0, Co = 0, kr = null, _e = null, Eo = 0, Dt = 1 / 0, Mn = null, Cl = !1, zo = null, Gn = null, El = !1, Yn = null, zl = 0, Sr = 0, Ro = null, Rl = -1, Pl = 0;
  function Qe() {
    return ($ & 6) !== 0 ? Se() : Rl !== -1 ? Rl : Rl = Se();
  }
  function bn(e) {
    return (e.mode & 1) === 0 ? 1 : ($ & 2) !== 0 && Ve !== 0 ? Ve & -Ve : Td.transition !== null ? (Pl === 0 && (Pl = ks()), Pl) : (e = le, e !== 0 || (e = window.event, e = e === void 0 ? 16 : Ts(e.type)), e);
  }
  function wn(e, n, t, r) {
    if (50 < Sr) throw Sr = 0, Ro = null, Error(c(185));
    Jt(e, t, r), (($ & 2) === 0 || e !== Fe) && (e === Fe && (($ & 2) === 0 && (Nl |= t), Pe === 4 && _n(e, Ve)), $e(e, r), t === 1 && $ === 0 && (n.mode & 1) === 0 && (Dt = Se() + 500, rl && Zn()));
  }
  function $e(e, n) {
    var t = e.callbackNode;
    Tc(e, n);
    var r = Vr(e, e === Fe ? Ve : 0);
    if (r === 0) t !== null && ys(t), e.callbackNode = null, e.callbackPriority = 0;
    else if (n = r & -r, e.callbackPriority !== n) {
      if (t != null && ys(t), n === 1) e.tag === 0 ? Pd(Ta.bind(null, e)) : mu(Ta.bind(null, e)), Cd(function() {
        ($ & 6) === 0 && Zn();
      }), t = null;
      else {
        switch (Ss(r)) {
          case 1:
            t = oi;
            break;
          case 4:
            t = xs;
            break;
          case 16:
            t = Mr;
            break;
          case 536870912:
            t = ws;
            break;
          default:
            t = Mr;
        }
        t = Va(t, Pa.bind(null, e));
      }
      e.callbackPriority = n, e.callbackNode = t;
    }
  }
  function Pa(e, n) {
    if (Rl = -1, Pl = 0, ($ & 6) !== 0) throw Error(c(327));
    var t = e.callbackNode;
    if (Vt() && e.callbackNode !== t) return null;
    var r = Vr(e, e === Fe ? Ve : 0);
    if (r === 0) return null;
    if ((r & 30) !== 0 || (r & e.expiredLanes) !== 0 || n) n = Tl(e, r);
    else {
      n = r;
      var l = $;
      $ |= 2;
      var i = Oa();
      (Fe !== e || Ve !== n) && (Mn = null, Dt = Se() + 500, dt(e, n));
      do
        try {
          Yd();
          break;
        } catch (d) {
          La(e, d);
        }
      while (!0);
      Zi(), jl.current = i, $ = l, Ee !== null ? n = 0 : (Fe = null, Ve = 0, n = Pe);
    }
    if (n !== 0) {
      if (n === 2 && (l = si(e), l !== 0 && (r = l, n = Po(e, l))), n === 1) throw t = wr, dt(e, 0), _n(e, r), $e(e, Se()), t;
      if (n === 6) _n(e, r);
      else {
        if (l = e.current.alternate, (r & 30) === 0 && !Qd(l) && (n = Tl(e, r), n === 2 && (i = si(e), i !== 0 && (r = i, n = Po(e, i))), n === 1)) throw t = wr, dt(e, 0), _n(e, r), $e(e, Se()), t;
        switch (e.finishedWork = l, e.finishedLanes = r, n) {
          case 0:
          case 1:
            throw Error(c(345));
          case 2:
            ft(e, _e, Mn);
            break;
          case 3:
            if (_n(e, r), (r & 130023424) === r && (n = Eo + 500 - Se(), 10 < n)) {
              if (Vr(e, 0) !== 0) break;
              if (l = e.suspendedLanes, (l & r) !== r) {
                Qe(), e.pingedLanes |= e.suspendedLanes & l;
                break;
              }
              e.timeoutHandle = Mi(ft.bind(null, e, _e, Mn), n);
              break;
            }
            ft(e, _e, Mn);
            break;
          case 4:
            if (_n(e, r), (r & 4194240) === r) break;
            for (n = e.eventTimes, l = -1; 0 < r; ) {
              var s = 31 - hn(r);
              i = 1 << s, s = n[s], s > l && (l = s), r &= ~i;
            }
            if (r = l, r = Se() - r, r = (120 > r ? 120 : 480 > r ? 480 : 1080 > r ? 1080 : 1920 > r ? 1920 : 3e3 > r ? 3e3 : 4320 > r ? 4320 : 1960 * Kd(r / 1960)) - r, 10 < r) {
              e.timeoutHandle = Mi(ft.bind(null, e, _e, Mn), r);
              break;
            }
            ft(e, _e, Mn);
            break;
          case 5:
            ft(e, _e, Mn);
            break;
          default:
            throw Error(c(329));
        }
      }
    }
    return $e(e, Se()), e.callbackNode === t ? Pa.bind(null, e) : null;
  }
  function Po(e, n) {
    var t = kr;
    return e.current.memoizedState.isDehydrated && (dt(e, n).flags |= 256), e = Tl(e, n), e !== 2 && (n = _e, _e = t, n !== null && To(n)), e;
  }
  function To(e) {
    _e === null ? _e = e : _e.push.apply(_e, e);
  }
  function Qd(e) {
    for (var n = e; ; ) {
      if (n.flags & 16384) {
        var t = n.updateQueue;
        if (t !== null && (t = t.stores, t !== null)) for (var r = 0; r < t.length; r++) {
          var l = t[r], i = l.getSnapshot;
          l = l.value;
          try {
            if (!mn(i(), l)) return !1;
          } catch {
            return !1;
          }
        }
      }
      if (t = n.child, n.subtreeFlags & 16384 && t !== null) t.return = n, n = t;
      else {
        if (n === e) break;
        for (; n.sibling === null; ) {
          if (n.return === null || n.return === e) return !0;
          n = n.return;
        }
        n.sibling.return = n.return, n = n.sibling;
      }
    }
    return !0;
  }
  function _n(e, n) {
    for (n &= ~Co, n &= ~Nl, e.suspendedLanes |= n, e.pingedLanes &= ~n, e = e.expirationTimes; 0 < n; ) {
      var t = 31 - hn(n), r = 1 << t;
      e[t] = -1, n &= ~r;
    }
  }
  function Ta(e) {
    if (($ & 6) !== 0) throw Error(c(327));
    Vt();
    var n = Vr(e, 0);
    if ((n & 1) === 0) return $e(e, Se()), null;
    var t = Tl(e, n);
    if (e.tag !== 0 && t === 2) {
      var r = si(e);
      r !== 0 && (n = r, t = Po(e, r));
    }
    if (t === 1) throw t = wr, dt(e, 0), _n(e, n), $e(e, Se()), t;
    if (t === 6) throw Error(c(345));
    return e.finishedWork = e.current.alternate, e.finishedLanes = n, ft(e, _e, Mn), $e(e, Se()), null;
  }
  function Lo(e, n) {
    var t = $;
    $ |= 1;
    try {
      return e(n);
    } finally {
      $ = t, $ === 0 && (Dt = Se() + 500, rl && Zn());
    }
  }
  function ct(e) {
    Yn !== null && Yn.tag === 0 && ($ & 6) === 0 && Vt();
    var n = $;
    $ |= 1;
    var t = fn.transition, r = le;
    try {
      if (fn.transition = null, le = 1, e) return e();
    } finally {
      le = r, fn.transition = t, $ = n, ($ & 6) === 0 && Zn();
    }
  }
  function Oo() {
    sn = Wt.current, de(Wt);
  }
  function dt(e, n) {
    e.finishedWork = null, e.finishedLanes = 0;
    var t = e.timeoutHandle;
    if (t !== -1 && (e.timeoutHandle = -1, Nd(t)), Ee !== null) for (t = Ee.return; t !== null; ) {
      var r = t;
      switch (qi(r), r.tag) {
        case 1:
          r = r.type.childContextTypes, r != null && nl();
          break;
        case 3:
          Ft(), de(Ge), de(qe), $i();
          break;
        case 5:
          bi(r);
          break;
        case 4:
          Ft();
          break;
        case 13:
          de(ye);
          break;
        case 19:
          de(ye);
          break;
        case 10:
          Ji(r.type._context);
          break;
        case 22:
        case 23:
          Oo();
      }
      t = t.return;
    }
    if (Fe = e, Ee = e = $n(e.current, null), Ve = sn = n, Pe = 0, wr = null, Co = Nl = at = 0, _e = kr = null, ot !== null) {
      for (n = 0; n < ot.length; n++) if (t = ot[n], r = t.interleaved, r !== null) {
        t.interleaved = null;
        var l = r.next, i = t.pending;
        if (i !== null) {
          var s = i.next;
          i.next = l, r.next = s;
        }
        t.pending = r;
      }
      ot = null;
    }
    return e;
  }
  function La(e, n) {
    do {
      var t = Ee;
      try {
        if (Zi(), pl.current = gl, hl) {
          for (var r = xe.memoizedState; r !== null; ) {
            var l = r.queue;
            l !== null && (l.pending = null), r = r.next;
          }
          hl = !1;
        }
        if (ut = 0, Oe = Re = xe = null, hr = !1, mr = 0, No.current = null, t === null || t.return === null) {
          Pe = 1, wr = n, Ee = null;
          break;
        }
        e: {
          var i = e, s = t.return, d = t, f = n;
          if (n = Ve, d.flags |= 32768, f !== null && typeof f == "object" && typeof f.then == "function") {
            var y = f, N = d, C = N.tag;
            if ((N.mode & 1) === 0 && (C === 0 || C === 11 || C === 15)) {
              var j = N.alternate;
              j ? (N.updateQueue = j.updateQueue, N.memoizedState = j.memoizedState, N.lanes = j.lanes) : (N.updateQueue = null, N.memoizedState = null);
            }
            var F = ta(s);
            if (F !== null) {
              F.flags &= -257, ra(F, s, d, i, n), F.mode & 1 && na(i, y, n), n = F, f = y;
              var I = n.updateQueue;
              if (I === null) {
                var W = /* @__PURE__ */ new Set();
                W.add(f), n.updateQueue = W;
              } else I.add(f);
              break e;
            } else {
              if ((n & 1) === 0) {
                na(i, y, n), Fo();
                break e;
              }
              f = Error(c(426));
            }
          } else if (me && d.mode & 1) {
            var je = ta(s);
            if (je !== null) {
              (je.flags & 65536) === 0 && (je.flags |= 256), ra(je, s, d, i, n), Bi(Mt(f, d));
              break e;
            }
          }
          i = f = Mt(f, d), Pe !== 4 && (Pe = 2), kr === null ? kr = [i] : kr.push(i), i = s;
          do {
            switch (i.tag) {
              case 3:
                i.flags |= 65536, n &= -n, i.lanes |= n;
                var m = $u(i, f, n);
                Eu(i, m);
                break e;
              case 1:
                d = f;
                var p = i.type, v = i.stateNode;
                if ((i.flags & 128) === 0 && (typeof p.getDerivedStateFromError == "function" || v !== null && typeof v.componentDidCatch == "function" && (Gn === null || !Gn.has(v)))) {
                  i.flags |= 65536, n &= -n, i.lanes |= n;
                  var R = ea(i, d, n);
                  Eu(i, R);
                  break e;
                }
            }
            i = i.return;
          } while (i !== null);
        }
        Ma(t);
      } catch (D) {
        n = D, Ee === t && t !== null && (Ee = t = t.return);
        continue;
      }
      break;
    } while (!0);
  }
  function Oa() {
    var e = jl.current;
    return jl.current = gl, e === null ? gl : e;
  }
  function Fo() {
    (Pe === 0 || Pe === 3 || Pe === 2) && (Pe = 4), Fe === null || (at & 268435455) === 0 && (Nl & 268435455) === 0 || _n(Fe, Ve);
  }
  function Tl(e, n) {
    var t = $;
    $ |= 2;
    var r = Oa();
    (Fe !== e || Ve !== n) && (Mn = null, dt(e, n));
    do
      try {
        Gd();
        break;
      } catch (l) {
        La(e, l);
      }
    while (!0);
    if (Zi(), $ = t, jl.current = r, Ee !== null) throw Error(c(261));
    return Fe = null, Ve = 0, Pe;
  }
  function Gd() {
    for (; Ee !== null; ) Fa(Ee);
  }
  function Yd() {
    for (; Ee !== null && !kc(); ) Fa(Ee);
  }
  function Fa(e) {
    var n = Da(e.alternate, e, sn);
    e.memoizedProps = e.pendingProps, n === null ? Ma(e) : Ee = n, No.current = null;
  }
  function Ma(e) {
    var n = e;
    do {
      var t = n.alternate;
      if (e = n.return, (n.flags & 32768) === 0) {
        if (t = Ad(t, n, sn), t !== null) {
          Ee = t;
          return;
        }
      } else {
        if (t = Bd(t, n), t !== null) {
          t.flags &= 32767, Ee = t;
          return;
        }
        if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
        else {
          Pe = 6, Ee = null;
          return;
        }
      }
      if (n = n.sibling, n !== null) {
        Ee = n;
        return;
      }
      Ee = n = e;
    } while (n !== null);
    Pe === 0 && (Pe = 5);
  }
  function ft(e, n, t) {
    var r = le, l = fn.transition;
    try {
      fn.transition = null, le = 1, bd(e, n, t, r);
    } finally {
      fn.transition = l, le = r;
    }
    return null;
  }
  function bd(e, n, t, r) {
    do
      Vt();
    while (Yn !== null);
    if (($ & 6) !== 0) throw Error(c(327));
    t = e.finishedWork;
    var l = e.finishedLanes;
    if (t === null) return null;
    if (e.finishedWork = null, e.finishedLanes = 0, t === e.current) throw Error(c(177));
    e.callbackNode = null, e.callbackPriority = 0;
    var i = t.lanes | t.childLanes;
    if (Lc(e, i), e === Fe && (Ee = Fe = null, Ve = 0), (t.subtreeFlags & 2064) === 0 && (t.flags & 2064) === 0 || El || (El = !0, Va(Mr, function() {
      return Vt(), null;
    })), i = (t.flags & 15990) !== 0, (t.subtreeFlags & 15990) !== 0 || i) {
      i = fn.transition, fn.transition = null;
      var s = le;
      le = 1;
      var d = $;
      $ |= 4, No.current = null, Zd(e, t), Na(t, e), gd(Oi), Hr = !!Li, Oi = Li = null, e.current = t, Jd(t), Sc(), $ = d, le = s, fn.transition = i;
    } else e.current = t;
    if (El && (El = !1, Yn = e, zl = l), i = e.pendingLanes, i === 0 && (Gn = null), Cc(t.stateNode), $e(e, Se()), n !== null) for (r = e.onRecoverableError, t = 0; t < n.length; t++) l = n[t], r(l.value, { componentStack: l.stack, digest: l.digest });
    if (Cl) throw Cl = !1, e = zo, zo = null, e;
    return (zl & 1) !== 0 && e.tag !== 0 && Vt(), i = e.pendingLanes, (i & 1) !== 0 ? e === Ro ? Sr++ : (Sr = 0, Ro = e) : Sr = 0, Zn(), null;
  }
  function Vt() {
    if (Yn !== null) {
      var e = Ss(zl), n = fn.transition, t = le;
      try {
        if (fn.transition = null, le = 16 > e ? 16 : e, Yn === null) var r = !1;
        else {
          if (e = Yn, Yn = null, zl = 0, ($ & 6) !== 0) throw Error(c(331));
          var l = $;
          for ($ |= 4, M = e.current; M !== null; ) {
            var i = M, s = i.child;
            if ((M.flags & 16) !== 0) {
              var d = i.deletions;
              if (d !== null) {
                for (var f = 0; f < d.length; f++) {
                  var y = d[f];
                  for (M = y; M !== null; ) {
                    var N = M;
                    switch (N.tag) {
                      case 0:
                      case 11:
                      case 15:
                        xr(8, N, i);
                    }
                    var C = N.child;
                    if (C !== null) C.return = N, M = C;
                    else for (; M !== null; ) {
                      N = M;
                      var j = N.sibling, F = N.return;
                      if (xa(N), N === y) {
                        M = null;
                        break;
                      }
                      if (j !== null) {
                        j.return = F, M = j;
                        break;
                      }
                      M = F;
                    }
                  }
                }
                var I = i.alternate;
                if (I !== null) {
                  var W = I.child;
                  if (W !== null) {
                    I.child = null;
                    do {
                      var je = W.sibling;
                      W.sibling = null, W = je;
                    } while (W !== null);
                  }
                }
                M = i;
              }
            }
            if ((i.subtreeFlags & 2064) !== 0 && s !== null) s.return = i, M = s;
            else e: for (; M !== null; ) {
              if (i = M, (i.flags & 2048) !== 0) switch (i.tag) {
                case 0:
                case 11:
                case 15:
                  xr(9, i, i.return);
              }
              var m = i.sibling;
              if (m !== null) {
                m.return = i.return, M = m;
                break e;
              }
              M = i.return;
            }
          }
          var p = e.current;
          for (M = p; M !== null; ) {
            s = M;
            var v = s.child;
            if ((s.subtreeFlags & 2064) !== 0 && v !== null) v.return = s, M = v;
            else e: for (s = p; M !== null; ) {
              if (d = M, (d.flags & 2048) !== 0) try {
                switch (d.tag) {
                  case 0:
                  case 11:
                  case 15:
                    Sl(9, d);
                }
              } catch (D) {
                we(d, d.return, D);
              }
              if (d === s) {
                M = null;
                break e;
              }
              var R = d.sibling;
              if (R !== null) {
                R.return = d.return, M = R;
                break e;
              }
              M = d.return;
            }
          }
          if ($ = l, Zn(), Sn && typeof Sn.onPostCommitFiberRoot == "function") try {
            Sn.onPostCommitFiberRoot(Ir, e);
          } catch {
          }
          r = !0;
        }
        return r;
      } finally {
        le = t, fn.transition = n;
      }
    }
    return !1;
  }
  function Ia(e, n, t) {
    n = Mt(t, n), n = $u(e, n, 1), e = Kn(e, n, 1), n = Qe(), e !== null && (Jt(e, 1, n), $e(e, n));
  }
  function we(e, n, t) {
    if (e.tag === 3) Ia(e, e, t);
    else for (; n !== null; ) {
      if (n.tag === 3) {
        Ia(n, e, t);
        break;
      } else if (n.tag === 1) {
        var r = n.stateNode;
        if (typeof n.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (Gn === null || !Gn.has(r))) {
          e = Mt(t, e), e = ea(n, e, 1), n = Kn(n, e, 1), e = Qe(), n !== null && (Jt(n, 1, e), $e(n, e));
          break;
        }
      }
      n = n.return;
    }
  }
  function _d(e, n, t) {
    var r = e.pingCache;
    r !== null && r.delete(n), n = Qe(), e.pingedLanes |= e.suspendedLanes & t, Fe === e && (Ve & t) === t && (Pe === 4 || Pe === 3 && (Ve & 130023424) === Ve && 500 > Se() - Eo ? dt(e, 0) : Co |= t), $e(e, n);
  }
  function Wa(e, n) {
    n === 0 && ((e.mode & 1) === 0 ? n = 1 : (n = Dr, Dr <<= 1, (Dr & 130023424) === 0 && (Dr = 4194304)));
    var t = Qe();
    e = Ln(e, n), e !== null && (Jt(e, n, t), $e(e, t));
  }
  function $d(e) {
    var n = e.memoizedState, t = 0;
    n !== null && (t = n.retryLane), Wa(e, t);
  }
  function ef(e, n) {
    var t = 0;
    switch (e.tag) {
      case 13:
        var r = e.stateNode, l = e.memoizedState;
        l !== null && (t = l.retryLane);
        break;
      case 19:
        r = e.stateNode;
        break;
      default:
        throw Error(c(314));
    }
    r !== null && r.delete(n), Wa(e, t);
  }
  var Da;
  Da = function(e, n, t) {
    if (e !== null) if (e.memoizedProps !== n.pendingProps || Ge.current) be = !0;
    else {
      if ((e.lanes & t) === 0 && (n.flags & 128) === 0) return be = !1, Hd(e, n, t);
      be = (e.flags & 131072) !== 0;
    }
    else be = !1, me && (n.flags & 1048576) !== 0 && vu(n, il, n.index);
    switch (n.lanes = 0, n.tag) {
      case 2:
        var r = n.type;
        wl(e, n), e = n.pendingProps;
        var l = Et(n, qe.current);
        Ot(n, t), l = to(null, n, r, e, l, t);
        var i = ro();
        return n.flags |= 1, typeof l == "object" && l !== null && typeof l.render == "function" && l.$$typeof === void 0 ? (n.tag = 1, n.memoizedState = null, n.updateQueue = null, Ye(r) ? (i = !0, tl(n)) : i = !1, n.memoizedState = l.state !== null && l.state !== void 0 ? l.state : null, Gi(n), l.updater = yl, n.stateNode = l, l._reactInternals = n, ao(n, r, e, t), n = ho(null, n, r, !0, i, t)) : (n.tag = 0, me && i && Ui(n), Ke(null, n, l, t), n = n.child), n;
      case 16:
        r = n.elementType;
        e: {
          switch (wl(e, n), e = n.pendingProps, l = r._init, r = l(r._payload), n.type = r, l = n.tag = tf(r), e = gn(r, e), l) {
            case 0:
              n = po(null, n, r, e, t);
              break e;
            case 1:
              n = aa(null, n, r, e, t);
              break e;
            case 11:
              n = la(null, n, r, e, t);
              break e;
            case 14:
              n = ia(null, n, r, gn(r.type, e), t);
              break e;
          }
          throw Error(c(
            306,
            r,
            ""
          ));
        }
        return n;
      case 0:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), po(e, n, r, l, t);
      case 1:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), aa(e, n, r, l, t);
      case 3:
        e: {
          if (ca(n), e === null) throw Error(c(387));
          r = n.pendingProps, i = n.memoizedState, l = i.element, Cu(e, n), dl(n, r, null, t);
          var s = n.memoizedState;
          if (r = s.element, i.isDehydrated) if (i = { element: r, isDehydrated: !1, cache: s.cache, pendingSuspenseBoundaries: s.pendingSuspenseBoundaries, transitions: s.transitions }, n.updateQueue.baseState = i, n.memoizedState = i, n.flags & 256) {
            l = Mt(Error(c(423)), n), n = da(e, n, r, t, l);
            break e;
          } else if (r !== l) {
            l = Mt(Error(c(424)), n), n = da(e, n, r, t, l);
            break e;
          } else for (on = An(n.stateNode.containerInfo.firstChild), ln = n, me = !0, vn = null, t = ju(n, null, r, t), n.child = t; t; ) t.flags = t.flags & -3 | 4096, t = t.sibling;
          else {
            if (Pt(), r === l) {
              n = Fn(e, n, t);
              break e;
            }
            Ke(e, n, r, t);
          }
          n = n.child;
        }
        return n;
      case 5:
        return Ru(n), e === null && Ai(n), r = n.type, l = n.pendingProps, i = e !== null ? e.memoizedProps : null, s = l.children, Fi(r, l) ? s = null : i !== null && Fi(r, i) && (n.flags |= 32), ua(e, n), Ke(e, n, s, t), n.child;
      case 6:
        return e === null && Ai(n), null;
      case 13:
        return fa(e, n, t);
      case 4:
        return Yi(n, n.stateNode.containerInfo), r = n.pendingProps, e === null ? n.child = Tt(n, null, r, t) : Ke(e, n, r, t), n.child;
      case 11:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), la(e, n, r, l, t);
      case 7:
        return Ke(e, n, n.pendingProps, t), n.child;
      case 8:
        return Ke(e, n, n.pendingProps.children, t), n.child;
      case 12:
        return Ke(e, n, n.pendingProps.children, t), n.child;
      case 10:
        e: {
          if (r = n.type._context, l = n.pendingProps, i = n.memoizedProps, s = l.value, se(ul, r._currentValue), r._currentValue = s, i !== null) if (mn(i.value, s)) {
            if (i.children === l.children && !Ge.current) {
              n = Fn(e, n, t);
              break e;
            }
          } else for (i = n.child, i !== null && (i.return = n); i !== null; ) {
            var d = i.dependencies;
            if (d !== null) {
              s = i.child;
              for (var f = d.firstContext; f !== null; ) {
                if (f.context === r) {
                  if (i.tag === 1) {
                    f = On(-1, t & -t), f.tag = 2;
                    var y = i.updateQueue;
                    if (y !== null) {
                      y = y.shared;
                      var N = y.pending;
                      N === null ? f.next = f : (f.next = N.next, N.next = f), y.pending = f;
                    }
                  }
                  i.lanes |= t, f = i.alternate, f !== null && (f.lanes |= t), Ki(
                    i.return,
                    t,
                    n
                  ), d.lanes |= t;
                  break;
                }
                f = f.next;
              }
            } else if (i.tag === 10) s = i.type === n.type ? null : i.child;
            else if (i.tag === 18) {
              if (s = i.return, s === null) throw Error(c(341));
              s.lanes |= t, d = s.alternate, d !== null && (d.lanes |= t), Ki(s, t, n), s = i.sibling;
            } else s = i.child;
            if (s !== null) s.return = i;
            else for (s = i; s !== null; ) {
              if (s === n) {
                s = null;
                break;
              }
              if (i = s.sibling, i !== null) {
                i.return = s.return, s = i;
                break;
              }
              s = s.return;
            }
            i = s;
          }
          Ke(e, n, l.children, t), n = n.child;
        }
        return n;
      case 9:
        return l = n.type, r = n.pendingProps.children, Ot(n, t), l = cn(l), r = r(l), n.flags |= 1, Ke(e, n, r, t), n.child;
      case 14:
        return r = n.type, l = gn(r, n.pendingProps), l = gn(r.type, l), ia(e, n, r, l, t);
      case 15:
        return oa(e, n, n.type, n.pendingProps, t);
      case 17:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : gn(r, l), wl(e, n), n.tag = 1, Ye(r) ? (e = !0, tl(n)) : e = !1, Ot(n, t), bu(n, r, l), ao(n, r, l, t), ho(null, n, r, !0, e, t);
      case 19:
        return ha(e, n, t);
      case 22:
        return sa(e, n, t);
    }
    throw Error(c(156, n.tag));
  };
  function Va(e, n) {
    return gs(e, n);
  }
  function nf(e, n, t, r) {
    this.tag = e, this.key = t, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = n, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
  }
  function pn(e, n, t, r) {
    return new nf(e, n, t, r);
  }
  function Mo(e) {
    return e = e.prototype, !(!e || !e.isReactComponent);
  }
  function tf(e) {
    if (typeof e == "function") return Mo(e) ? 1 : 0;
    if (e != null) {
      if (e = e.$$typeof, e === ze) return 11;
      if (e === Le) return 14;
    }
    return 2;
  }
  function $n(e, n) {
    var t = e.alternate;
    return t === null ? (t = pn(e.tag, n, e.key, e.mode), t.elementType = e.elementType, t.type = e.type, t.stateNode = e.stateNode, t.alternate = e, e.alternate = t) : (t.pendingProps = n, t.type = e.type, t.flags = 0, t.subtreeFlags = 0, t.deletions = null), t.flags = e.flags & 14680064, t.childLanes = e.childLanes, t.lanes = e.lanes, t.child = e.child, t.memoizedProps = e.memoizedProps, t.memoizedState = e.memoizedState, t.updateQueue = e.updateQueue, n = e.dependencies, t.dependencies = n === null ? null : { lanes: n.lanes, firstContext: n.firstContext }, t.sibling = e.sibling, t.index = e.index, t.ref = e.ref, t;
  }
  function Ll(e, n, t, r, l, i) {
    var s = 2;
    if (r = e, typeof e == "function") Mo(e) && (s = 1);
    else if (typeof e == "string") s = 5;
    else e: switch (e) {
      case pe:
        return pt(t.children, l, i, n);
      case Q:
        s = 8, l |= 8;
        break;
      case Ze:
        return e = pn(12, t, n, l | 2), e.elementType = Ze, e.lanes = i, e;
      case V:
        return e = pn(13, t, n, l), e.elementType = V, e.lanes = i, e;
      case _:
        return e = pn(19, t, n, l), e.elementType = _, e.lanes = i, e;
      case ae:
        return Ol(t, l, i, n);
      default:
        if (typeof e == "object" && e !== null) switch (e.$$typeof) {
          case We:
            s = 10;
            break e;
          case Je:
            s = 9;
            break e;
          case ze:
            s = 11;
            break e;
          case Le:
            s = 14;
            break e;
          case Ce:
            s = 16, r = null;
            break e;
        }
        throw Error(c(130, e == null ? e : typeof e, ""));
    }
    return n = pn(s, t, n, l), n.elementType = e, n.type = r, n.lanes = i, n;
  }
  function pt(e, n, t, r) {
    return e = pn(7, e, r, n), e.lanes = t, e;
  }
  function Ol(e, n, t, r) {
    return e = pn(22, e, r, n), e.elementType = ae, e.lanes = t, e.stateNode = { isHidden: !1 }, e;
  }
  function Io(e, n, t) {
    return e = pn(6, e, null, n), e.lanes = t, e;
  }
  function Wo(e, n, t) {
    return n = pn(4, e.children !== null ? e.children : [], e.key, n), n.lanes = t, n.stateNode = { containerInfo: e.containerInfo, pendingChildren: null, implementation: e.implementation }, n;
  }
  function rf(e, n, t, r, l) {
    this.tag = n, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = ui(0), this.expirationTimes = ui(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = ui(0), this.identifierPrefix = r, this.onRecoverableError = l, this.mutableSourceEagerHydrationData = null;
  }
  function Do(e, n, t, r, l, i, s, d, f) {
    return e = new rf(e, n, t, d, f), n === 1 ? (n = 1, i === !0 && (n |= 8)) : n = 0, i = pn(3, null, null, n), e.current = i, i.stateNode = e, i.memoizedState = { element: r, isDehydrated: t, cache: null, transitions: null, pendingSuspenseBoundaries: null }, Gi(i), e;
  }
  function lf(e, n, t) {
    var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
    return { $$typeof: ke, key: r == null ? null : "" + r, children: e, containerInfo: n, implementation: t };
  }
  function Ua(e) {
    if (!e) return Xn;
    e = e._reactInternals;
    e: {
      if (nt(e) !== e || e.tag !== 1) throw Error(c(170));
      var n = e;
      do {
        switch (n.tag) {
          case 3:
            n = n.stateNode.context;
            break e;
          case 1:
            if (Ye(n.type)) {
              n = n.stateNode.__reactInternalMemoizedMergedChildContext;
              break e;
            }
        }
        n = n.return;
      } while (n !== null);
      throw Error(c(171));
    }
    if (e.tag === 1) {
      var t = e.type;
      if (Ye(t)) return pu(e, t, n);
    }
    return n;
  }
  function qa(e, n, t, r, l, i, s, d, f) {
    return e = Do(t, r, !0, e, l, i, s, d, f), e.context = Ua(null), t = e.current, r = Qe(), l = bn(t), i = On(r, l), i.callback = n ?? null, Kn(t, i, l), e.current.lanes = l, Jt(e, l, r), $e(e, r), e;
  }
  function Fl(e, n, t, r) {
    var l = n.current, i = Qe(), s = bn(l);
    return t = Ua(t), n.context === null ? n.context = t : n.pendingContext = t, n = On(i, s), n.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (n.callback = r), e = Kn(l, n, s), e !== null && (wn(e, l, s, i), cl(e, l, s)), s;
  }
  function Ml(e) {
    if (e = e.current, !e.child) return null;
    switch (e.child.tag) {
      case 5:
        return e.child.stateNode;
      default:
        return e.child.stateNode;
    }
  }
  function Ha(e, n) {
    if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
      var t = e.retryLane;
      e.retryLane = t !== 0 && t < n ? t : n;
    }
  }
  function Vo(e, n) {
    Ha(e, n), (e = e.alternate) && Ha(e, n);
  }
  function of() {
    return null;
  }
  var Aa = typeof reportError == "function" ? reportError : function(e) {
    console.error(e);
  };
  function Uo(e) {
    this._internalRoot = e;
  }
  Il.prototype.render = Uo.prototype.render = function(e) {
    var n = this._internalRoot;
    if (n === null) throw Error(c(409));
    Fl(e, n, null, null);
  }, Il.prototype.unmount = Uo.prototype.unmount = function() {
    var e = this._internalRoot;
    if (e !== null) {
      this._internalRoot = null;
      var n = e.containerInfo;
      ct(function() {
        Fl(null, e, null, null);
      }), n[zn] = null;
    }
  };
  function Il(e) {
    this._internalRoot = e;
  }
  Il.prototype.unstable_scheduleHydration = function(e) {
    if (e) {
      var n = Cs();
      e = { blockedOn: null, target: e, priority: n };
      for (var t = 0; t < Un.length && n !== 0 && n < Un[t].priority; t++) ;
      Un.splice(t, 0, e), t === 0 && Rs(e);
    }
  };
  function qo(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
  }
  function Wl(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
  }
  function Ba() {
  }
  function sf(e, n, t, r, l) {
    if (l) {
      if (typeof r == "function") {
        var i = r;
        r = function() {
          var y = Ml(s);
          i.call(y);
        };
      }
      var s = qa(n, r, e, 0, null, !1, !1, "", Ba);
      return e._reactRootContainer = s, e[zn] = s.current, or(e.nodeType === 8 ? e.parentNode : e), ct(), s;
    }
    for (; l = e.lastChild; ) e.removeChild(l);
    if (typeof r == "function") {
      var d = r;
      r = function() {
        var y = Ml(f);
        d.call(y);
      };
    }
    var f = Do(e, 0, !1, null, null, !1, !1, "", Ba);
    return e._reactRootContainer = f, e[zn] = f.current, or(e.nodeType === 8 ? e.parentNode : e), ct(function() {
      Fl(n, f, t, r);
    }), f;
  }
  function Dl(e, n, t, r, l) {
    var i = t._reactRootContainer;
    if (i) {
      var s = i;
      if (typeof l == "function") {
        var d = l;
        l = function() {
          var f = Ml(s);
          d.call(f);
        };
      }
      Fl(n, s, e, l);
    } else s = sf(t, n, e, l, r);
    return Ml(s);
  }
  js = function(e) {
    switch (e.tag) {
      case 3:
        var n = e.stateNode;
        if (n.current.memoizedState.isDehydrated) {
          var t = Zt(n.pendingLanes);
          t !== 0 && (ai(n, t | 1), $e(n, Se()), ($ & 6) === 0 && (Dt = Se() + 500, Zn()));
        }
        break;
      case 13:
        ct(function() {
          var r = Ln(e, 1);
          if (r !== null) {
            var l = Qe();
            wn(r, e, 1, l);
          }
        }), Vo(e, 1);
    }
  }, ci = function(e) {
    if (e.tag === 13) {
      var n = Ln(e, 134217728);
      if (n !== null) {
        var t = Qe();
        wn(n, e, 134217728, t);
      }
      Vo(e, 134217728);
    }
  }, Ns = function(e) {
    if (e.tag === 13) {
      var n = bn(e), t = Ln(e, n);
      if (t !== null) {
        var r = Qe();
        wn(t, e, n, r);
      }
      Vo(e, n);
    }
  }, Cs = function() {
    return le;
  }, Es = function(e, n) {
    var t = le;
    try {
      return le = e, n();
    } finally {
      le = t;
    }
  }, ti = function(e, n, t) {
    switch (n) {
      case "input":
        if (Ql(e, t), n = t.name, t.type === "radio" && n != null) {
          for (t = e; t.parentNode; ) t = t.parentNode;
          for (t = t.querySelectorAll("input[name=" + JSON.stringify("" + n) + '][type="radio"]'), n = 0; n < t.length; n++) {
            var r = t[n];
            if (r !== e && r.form === e.form) {
              var l = el(r);
              if (!l) throw Error(c(90));
              Yo(r), Ql(r, l);
            }
          }
        }
        break;
      case "textarea":
        ns(e, t);
        break;
      case "select":
        n = t.value, n != null && ht(e, !!t.multiple, n, !1);
    }
  }, cs = Lo, ds = ct;
  var uf = { usingClientEntryPoint: !1, Events: [ar, Nt, el, us, as, Lo] }, jr = { findFiberByHostInstance: tt, bundleType: 0, version: "18.3.1", rendererPackageName: "react-dom" }, af = { bundleType: jr.bundleType, version: jr.version, rendererPackageName: jr.rendererPackageName, rendererConfig: jr.rendererConfig, overrideHookState: null, overrideHookStateDeletePath: null, overrideHookStateRenamePath: null, overrideProps: null, overridePropsDeletePath: null, overridePropsRenamePath: null, setErrorHandler: null, setSuspenseHandler: null, scheduleUpdate: null, currentDispatcherRef: fe.ReactCurrentDispatcher, findHostInstanceByFiber: function(e) {
    return e = ms(e), e === null ? null : e.stateNode;
  }, findFiberByHostInstance: jr.findFiberByHostInstance || of, findHostInstancesForRefresh: null, scheduleRefresh: null, scheduleRoot: null, setRefreshHandler: null, getCurrentFiber: null, reconcilerVersion: "18.3.1-next-f1338f8080-20240426" };
  if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
    var Vl = __REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (!Vl.isDisabled && Vl.supportsFiber) try {
      Ir = Vl.inject(af), Sn = Vl;
    } catch {
    }
  }
  return en.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = uf, en.createPortal = function(e, n) {
    var t = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
    if (!qo(n)) throw Error(c(200));
    return lf(e, n, null, t);
  }, en.createRoot = function(e, n) {
    if (!qo(e)) throw Error(c(299));
    var t = !1, r = "", l = Aa;
    return n != null && (n.unstable_strictMode === !0 && (t = !0), n.identifierPrefix !== void 0 && (r = n.identifierPrefix), n.onRecoverableError !== void 0 && (l = n.onRecoverableError)), n = Do(e, 1, !1, null, null, t, !1, r, l), e[zn] = n.current, or(e.nodeType === 8 ? e.parentNode : e), new Uo(n);
  }, en.findDOMNode = function(e) {
    if (e == null) return null;
    if (e.nodeType === 1) return e;
    var n = e._reactInternals;
    if (n === void 0)
      throw typeof e.render == "function" ? Error(c(188)) : (e = Object.keys(e).join(","), Error(c(268, e)));
    return e = ms(n), e = e === null ? null : e.stateNode, e;
  }, en.flushSync = function(e) {
    return ct(e);
  }, en.hydrate = function(e, n, t) {
    if (!Wl(n)) throw Error(c(200));
    return Dl(null, e, n, !0, t);
  }, en.hydrateRoot = function(e, n, t) {
    if (!qo(e)) throw Error(c(405));
    var r = t != null && t.hydratedSources || null, l = !1, i = "", s = Aa;
    if (t != null && (t.unstable_strictMode === !0 && (l = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (s = t.onRecoverableError)), n = qa(n, null, e, 1, t ?? null, l, !1, i, s), e[zn] = n.current, or(e), r) for (e = 0; e < r.length; e++) t = r[e], l = t._getVersion, l = l(t._source), n.mutableSourceEagerHydrationData == null ? n.mutableSourceEagerHydrationData = [t, l] : n.mutableSourceEagerHydrationData.push(
      t,
      l
    );
    return new Il(n);
  }, en.render = function(e, n, t) {
    if (!Wl(n)) throw Error(c(200));
    return Dl(null, e, n, !1, t);
  }, en.unmountComponentAtNode = function(e) {
    if (!Wl(e)) throw Error(c(40));
    return e._reactRootContainer ? (ct(function() {
      Dl(null, null, e, !1, function() {
        e._reactRootContainer = null, e[zn] = null;
      });
    }), !0) : !1;
  }, en.unstable_batchedUpdates = Lo, en.unstable_renderSubtreeIntoContainer = function(e, n, t, r) {
    if (!Wl(t)) throw Error(c(200));
    if (e == null || e._reactInternals === void 0) throw Error(c(38));
    return Dl(e, n, t, !1, r);
  }, en.version = "18.3.1-next-f1338f8080-20240426", en;
}
var ba;
function gf() {
  if (ba) return Bo.exports;
  ba = 1;
  function u() {
    if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
      try {
        __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(u);
      } catch (a) {
        console.error(a);
      }
  }
  return u(), Bo.exports = vf(), Bo.exports;
}
var _a;
function yf() {
  if (_a) return Ul;
  _a = 1;
  var u = gf();
  return Ul.createRoot = u.createRoot, Ul.hydrateRoot = u.hydrateRoot, Ul;
}
var xf = yf();
const wf = "data:image/png;base64,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", kf = "" + new URL("NotoColorEmoji-nature-Rpfd13Si.woff2", import.meta.url).href, Sf = "" + new URL("NotoColorEmoji-objects-EKxheXEn.woff2", import.meta.url).href, jf = { sans: 'Manrope, "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Avenir Next", "Segoe UI", sans-serif', mono: '"IBM Plex Mono", "SFMono-Regular", "SF Mono", Menlo, Consolas, monospace' }, Nf = { eyebrow: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, sectionLabel: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, pageTitle: { size: "1.375rem", weight: 650, lineHeight: "1.2", tracking: "-0.02em" }, subtitle: { size: "0.8125rem", weight: 450, lineHeight: "1.45", tracking: "0" }, body: { size: "0.9375rem", weight: 400, lineHeight: "1.6", tracking: "0" }, input: { size: "0.875rem", weight: 450, lineHeight: "1.5", tracking: "0" }, mono: { size: "0.75rem", weight: 600, lineHeight: "1.4", tracking: "0" }, scoreValue: { size: "1.25rem", weight: 600, lineHeight: "1", tracking: "-0.02em" }, scoreLabel: { size: "0.625rem", weight: 650, lineHeight: "1", tracking: "0.08em" }, footer: { size: "0.6875rem", weight: 450, lineHeight: "1.4", tracking: "0" } }, Cf = { card: "12px", input: "10px", panel: "16px", pill: "999px" }, Ef = { duration: { fast: "120ms", mid: "200ms", slow: "420ms" }, easing: { standard: "cubic-bezier(.2, .8, .2, 1)", entrance: "cubic-bezier(.22, .8, .2, 1)" } }, zf = { light: { washLow: "#FCEFD4", washHigh: "#F5B3A6", lineLow: "#E8A13C", lineHigh: "#D64540", safe: "#0E9384" }, dark: { washLow: "#4A3A1E", washHigh: "#4E2A26", lineLow: "#E0A24A", lineHigh: "#E8756B", safe: "#5FD6C6" } }, Rf = { light: { colorScheme: "light", canvas: "#FAF3F8", card: "#FFFFFF", surface: "rgba(255, 255, 255, 0.92)", surface2: "rgba(255, 255, 255, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(250, 243, 248, 0.78), rgba(250, 243, 248, 0.30) 82%)", ink: "#231A21", muted: "#6B5F68", faint: "#A395A0", line: "#F0DFEA", lineStrong: "#E2C8D8", brand: "#E562A8", brandBright: "#EF7CB8", brandWash: "#FBE7F2", safe: "#0E9384", safeWash: "#D7F0EB", warning: "#81520C", warningWash: "#FCEFD4", riskInk: "#D64540", riskWash: "#F8DDD7", focus: "#1B6ED1", link: "#0E9384", mint: "#AFDEDD", shadowColor: "rgba(65, 45, 61, 0.14)", shadowCard: "0 1px 2px rgba(16, 24, 40, 0.04)", shadowRaised: "0 22px 62px rgba(69, 37, 57, 0.12)", sidebarBg: "rgba(255, 255, 255, 0.92)", inputBg: "rgba(255, 255, 255, 0.96)", popoverBg: "rgba(255, 255, 255, 0.98)", optionHover: "rgba(229, 98, 168, 0.16)", btnBg: "rgba(229, 98, 168, 0.10)", btnHoverBg: "rgba(229, 98, 168, 0.20)", btnHoverBorder: "rgba(229, 98, 168, 0.50)", pillBg: "rgba(255, 255, 255, 0.70)", pillSelected: "linear-gradient(135deg, rgba(229, 98, 168, 0.22), rgba(14, 147, 132, 0.16))", pillSelectedBorder: "rgba(229, 98, 168, 0.55)", scrollThumb: "rgba(229, 98, 168, 0.50)", scrollThumb2: "rgba(229, 98, 168, 0.42)", scrollThumbHover: "rgba(229, 98, 168, 0.66)" }, dark: { colorScheme: "dark", canvas: "#151116", card: "#211A22", surface: "rgba(33, 26, 34, 0.92)", surface2: "rgba(33, 26, 34, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(18, 13, 20, 0.50), rgba(18, 13, 20, 0.10) 82%)", ink: "#F9F5F7", muted: "#B9ADB5", faint: "#8E8089", line: "rgba(255, 231, 242, 0.15)", lineStrong: "rgba(255, 231, 242, 0.26)", brand: "#F07EBB", brandBright: "#F79BCB", brandWash: "#4D2034", safe: "#5FD6C6", safeWash: "#173B37", warning: "#F0BE6D", warningWash: "#422F17", riskInk: "#FF9499", riskWash: "#4E2428", focus: "#6CAEFF", link: "#7FD8CA", mint: "#AFDEDD", shadowColor: "rgba(0, 0, 0, 0.50)", shadowCard: "0 1px 2px rgba(0, 0, 0, 0.30)", shadowRaised: "0 24px 70px rgba(0, 0, 0, 0.32)", sidebarBg: "rgba(21, 17, 22, 0.93)", inputBg: "rgba(20, 16, 24, 0.80)", popoverBg: "rgba(24, 18, 28, 0.97)", optionHover: "rgba(240, 126, 187, 0.22)", btnBg: "rgba(240, 126, 187, 0.16)", btnHoverBg: "rgba(240, 126, 187, 0.28)", btnHoverBorder: "rgba(240, 126, 187, 0.55)", pillBg: "rgba(33, 26, 34, 0.66)", pillSelected: "linear-gradient(135deg, rgba(240, 126, 187, 0.30), rgba(95, 214, 198, 0.20))", pillSelectedBorder: "rgba(240, 126, 187, 0.60)", scrollThumb: "rgba(240, 126, 187, 0.50)", scrollThumb2: "rgba(240, 126, 187, 0.42)", scrollThumbHover: "rgba(240, 126, 187, 0.66)" } }, nn = {
  fonts: jf,
  type: Nf,
  radii: Cf,
  motion: Ef,
  spanRamp: zf,
  palette: Rf
};
function $a(u) {
  const a = nn.palette[u], c = nn.spanRamp[u];
  return {
    "--canvas": a.canvas,
    "--surface": a.surface,
    "--surface-solid": a.card,
    "--ink": a.ink,
    "--muted": a.muted,
    "--faint": a.faint,
    "--line": a.line,
    "--line-strong": a.lineStrong,
    "--brand": a.brand,
    "--brand-bright": a.brandBright,
    "--brand-wash": a.brandWash,
    "--safe": a.safe,
    "--safe-wash": a.safeWash,
    "--warning": a.warning,
    "--warning-wash": a.warningWash,
    "--risk-ink": a.riskInk,
    "--risk-wash": a.riskWash,
    "--focus": a.focus,
    "--shadow": a.shadowRaised,
    "--shadow-whisper": a.shadowCard,
    "--span-wash-low": c.washLow,
    "--span-wash-high": c.washHigh,
    "--span-line-low": c.lineLow,
    "--span-line-high": c.lineHigh,
    "--span-safe": c.safe
  };
}
function Pf() {
  const u = {};
  for (const [a, c] of Object.entries(nn.type))
    u[`--text-${a}-size`] = c.size, u[`--text-${a}-weight`] = String(c.weight), u[`--text-${a}-line`] = c.lineHeight, u[`--text-${a}-tracking`] = c.tracking;
  return u;
}
function Tf() {
  return {
    "--font-sans": nn.fonts.sans,
    "--font-mono": nn.fonts.mono,
    "--radius-card": nn.radii.card,
    "--radius-input": nn.radii.input,
    "--radius-panel": nn.radii.panel,
    "--radius-pill": nn.radii.pill,
    "--dur-fast": nn.motion.duration.fast,
    "--dur-mid": nn.motion.duration.mid,
    "--dur-slow": nn.motion.duration.slow,
    "--ease-standard": nn.motion.easing.standard,
    "--ease-entrance": nn.motion.easing.entrance,
    ...Pf()
  };
}
function ec(u, a) {
  const c = Object.entries(a).map(([g, w]) => `  ${g}: ${w};`).join(`
`);
  return `${u} {
${c}
}`;
}
const Lf = [
  ec(".sirin-component-root", { ...Tf(), ...$a("light") }),
  ec(".sirin-workspace[data-theme='dark']", $a("dark"))
].join(`

`), uc = "recordedResultVerified", Of = {
  recordedResultVerified: "Recorded result · verified — detection not live"
};
let nc = !1;
function Ff(u) {
  if (u.querySelector(":scope > style[data-sirin-tokens]")) return;
  const a = document.createElement("style");
  a.setAttribute("data-sirin-tokens", ""), a.textContent = Lf, u.prepend(a);
}
function Mf() {
  if (nc || typeof FontFace > "u") return;
  nc = !0;
  const u = [
    new FontFace("Noto Color Emoji", `url(${Sf})`, { style: "normal", weight: "400", unicodeRange: "U+1F9EA" }),
    new FontFace("Noto Color Emoji", `url(${kf})`, { style: "normal", weight: "400", unicodeRange: "U+1F984" })
  ];
  for (const a of u)
    document.fonts.add(a), a.load().catch(() => document.fonts.delete(a));
}
const tc = {
  analyze: {
    task: "faithfulness",
    mode: "generate",
    exampleId: null,
    context: "",
    question: "",
    answer: "",
    prompt: "",
    sourceRunId: null
  }
}, If = { theme: "light", motion: "subtle" }, ac = 240, cc = 180, Wf = 400, rc = /* @__PURE__ */ new Set(), Df = /* @__PURE__ */ new Set(["consent_required", "busy", "empty_answer", "generation_unavailable", "judge_no_aligned_annotation", "provider_rate_limited", "provider_auth_failed"]), ql = /* @__PURE__ */ new Map();
function Vf(u) {
  return u ? { analyze: { ...tc.analyze, ...u.analyze, prompt: u.analyze.prompt ?? "", sourceRunId: u.analyze.sourceRunId ?? null }, quickPrompt: u.quickPrompt ?? "" } : { analyze: { ...tc.analyze }, quickPrompt: "" };
}
function lc() {
  var c, g, w, x;
  const u = (c = globalThis.sessionStorage) == null ? void 0 : c.getItem("sirin.client.id");
  if (u) return u;
  const a = ((w = (g = globalThis.crypto) == null ? void 0 : g.randomUUID) == null ? void 0 : w.call(g)) ?? `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return (x = globalThis.sessionStorage) == null || x.setItem("sirin.client.id", a), a;
}
function ic() {
  var u, a;
  return ((a = (u = globalThis.crypto) == null ? void 0 : u.randomUUID) == null ? void 0 : a.call(u)) ?? `action-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function Ue(u, a = !0) {
  return typeof u == "boolean" ? u : u && typeof u == "object" ? u.enabled : a;
}
function oc(u) {
  return u && typeof u == "object" ? u.reason ?? void 0 : void 0;
}
function In(u) {
  return u ? u.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (a) => a.toUpperCase()) : "Unavailable";
}
function Jo(u) {
  return u === "faithfulness" ? "Hallucination" : In(u);
}
function Ie(u) {
  return typeof u == "number" && Number.isFinite(u) ? u : null;
}
function Qo(u) {
  return Math.min(1, Math.max(0, u));
}
function dc(u) {
  return u >= 0.995 ? "1.0" : u.toFixed(2).replace(/^0+/, "");
}
function Rr(u, a, c) {
  return `color-mix(in srgb, var(${a}) ${Math.round(Qo(c) * 100)}%, var(${u}))`;
}
function Bl(u, a, c) {
  return a === !0 || u !== null && c !== null && u >= c;
}
function fc(u, a) {
  const c = a ?? 0;
  return Qo((u - c) / Math.max(1 - c, 1e-6));
}
function Er(u, a) {
  const c = Ie(u);
  return c === null ? "No score" : ["calibrated_probability", "calibratedProbability", "categorical_probabilities", "categoricalProbabilities"].includes(a ?? "") ? `${Math.round(c * 100)}%` : c.toFixed(c < 10 ? 2 : 1);
}
function Go(u, a) {
  const c = a == null ? void 0 : a.trim();
  return c || (["calibrated_probability", "calibratedProbability"].includes(u ?? "") ? "calibrated probability" : ["relative_within_answer", "relativeWithinAnswer"].includes(u ?? "") ? "relative within this answer — not comparable across runs" : ["thresholded_raw_score", "thresholdedRawScore"].includes(u ?? "") ? "raw score vs decision threshold τ" : ["categorical_probabilities", "categoricalProbabilities"].includes(u ?? "") ? "class confidence" : ["span_agreement", "spanAgreement"].includes(u ?? "") ? "judge agreement" : u === "verdict" ? "verdict" : null);
}
function Jl(u) {
  if (typeof u != "string") return "neutral";
  const a = u.trim().toLowerCase().replaceAll("_", " ").replaceAll("-", " ");
  return ["risk", "suspect", "unsupported", "hallucinated", "hallucination", "failed", "error", "unanswerable", "unsafe"].includes(a) ? "risk" : ["safe", "supported", "faithful", "answerable", "passed", "grounded", "healthy"].includes(a) ? "safe" : "neutral";
}
function Hl(u, a, c) {
  const g = (u == null ? void 0 : u[a]) ?? (u == null ? void 0 : u[c]);
  return g == null || g === "" ? "Not configured" : String(g);
}
function pc({ status: u }) {
  return /* @__PURE__ */ o.jsx("span", { className: `status-dot ${Jl(u)}`, "aria-hidden": "true" });
}
function Xe({ name: u }) {
  const a = {
    analyze: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M4 17.5 9 12l3 3 7-8" }),
      /* @__PURE__ */ o.jsx("path", { d: "M15 7h4v4" })
    ] }),
    runs: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M6 5h12M6 12h12M6 19h12" }),
      /* @__PURE__ */ o.jsx("path", { d: "M3 5h.01M3 12h.01M3 19h.01" })
    ] }),
    diagnostics: /* @__PURE__ */ o.jsx(o.Fragment, { children: /* @__PURE__ */ o.jsx("path", { d: "M4 14h3l2-7 4 11 2-7h5" }) }),
    arrow: /* @__PURE__ */ o.jsx(o.Fragment, { children: /* @__PURE__ */ o.jsx("path", { d: "m9 18 6-6-6-6" }) }),
    spark: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6Z" }),
      /* @__PURE__ */ o.jsx("path", { d: "m18 15 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7Z" })
    ] }),
    download: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M12 3v12m-5-5 5 5 5-5" }),
      /* @__PURE__ */ o.jsx("path", { d: "M5 21h14" })
    ] }),
    upload: /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("path", { d: "M12 21V9m-5 5 5-5 5 5" }),
      /* @__PURE__ */ o.jsx("path", { d: "M5 3h14" })
    ] })
  };
  return /* @__PURE__ */ o.jsx("svg", { className: "icon", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: a[u] });
}
function Uf({
  workspace: u,
  onWorkspace: a,
  setup: c,
  title: g,
  subtitle: w
}) {
  const [x, z] = ue.useState(!1), L = ue.useId();
  return ue.useEffect(() => {
    if (!x) return;
    const E = (k) => {
      k.key === "Escape" && z(!1);
    };
    return globalThis.addEventListener("keydown", E), () => globalThis.removeEventListener("keydown", E);
  }, [x]), /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
    /* @__PURE__ */ o.jsxs("header", { className: "shell-header", children: [
      /* @__PURE__ */ o.jsxs("button", { className: "brand", type: "button", onClick: () => a("analyze"), "aria-label": "SIRIN Analyze home", children: [
        /* @__PURE__ */ o.jsx("img", { src: wf, alt: "" }),
        /* @__PURE__ */ o.jsxs("span", { children: [
          /* @__PURE__ */ o.jsx("b", { children: "SIRIN" }),
          /* @__PURE__ */ o.jsx("small", { children: "Honesty, made visible." })
        ] })
      ] }),
      /* @__PURE__ */ o.jsx("nav", { className: "workspace-tabs", "aria-label": "Workspace", children: ["analyze", "runs", "diagnostics"].map((E) => /* @__PURE__ */ o.jsxs("button", { type: "button", "data-workspace-tab": E, className: u === E ? "active" : "", "aria-current": u === E ? "page" : void 0, onClick: () => a(E), children: [
        /* @__PURE__ */ o.jsx(Xe, { name: E }),
        In(E)
      ] }, E)) }),
      /* @__PURE__ */ o.jsxs("button", { className: "setup-chip", type: "button", onClick: () => z((E) => !E), "aria-expanded": x, "aria-controls": L, children: [
        /* @__PURE__ */ o.jsxs("span", { className: "setup-summary", children: [
          /* @__PURE__ */ o.jsx("small", { children: "Detector" }),
          /* @__PURE__ */ o.jsx("b", { children: Hl(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ o.jsx(Xe, { name: "arrow" })
      ] })
    ] }),
    x && /* @__PURE__ */ o.jsxs("div", { className: "setup-popover", id: L, role: "region", "aria-label": "Active setup", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Active setup" }),
      /* @__PURE__ */ o.jsxs("dl", { children: [
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Detector" }),
          /* @__PURE__ */ o.jsx("dd", { children: Hl(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Generator" }),
          /* @__PURE__ */ o.jsx("dd", { children: (c == null ? void 0 : c.providerLabel) ?? (c == null ? void 0 : c.modelId) ?? Hl(c, "modelLabel", "model") })
        ] }),
        /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Device" }),
          /* @__PURE__ */ o.jsx("dd", { children: (c == null ? void 0 : c.device) ?? "Automatic" })
        ] }),
        (c == null ? void 0 : c.layer) !== void 0 && c.layer !== null && /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Layer" }),
          /* @__PURE__ */ o.jsx("dd", { children: c.layer })
        ] }),
        (c == null ? void 0 : c.threshold) !== void 0 && c.threshold !== null && /* @__PURE__ */ o.jsxs("div", { children: [
          /* @__PURE__ */ o.jsx("dt", { children: "Threshold" }),
          /* @__PURE__ */ o.jsx("dd", { children: c.threshold })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsxs("section", { className: "page-head", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: u === "analyze" ? "Evidence workspace" : In(u) }),
      /* @__PURE__ */ o.jsx("h1", { children: g ?? (u === "analyze" ? "See where an answer leaves the evidence." : u === "runs" ? "Every result, with its receipts." : u === "compare" ? "Two detectors, one answer, side by side." : "Know what SIRIN is running.") }),
      /* @__PURE__ */ o.jsx("p", { children: w ?? (u === "analyze" ? "Generate or supply an answer. SIRIN checks it against context and makes uncertainty legible." : u === "runs" ? "Review immutable outcomes and carry portable records between sessions." : u === "compare" ? "Both detectors score the same answer. Localization overlap is comparable; scores are only compared when their scales are." : "Inspect the active runtime without exposing sensitive internals.") })
    ] })
  ] });
}
function kn({ label: u, hint: a, children: c }) {
  return /* @__PURE__ */ o.jsxs("label", { className: "field", children: [
    /* @__PURE__ */ o.jsxs("span", { children: [
      u,
      a && /* @__PURE__ */ o.jsx("small", { children: a })
    ] }),
    c
  ] });
}
function Al({ value: u, onChange: a, ariaLabel: c, children: g }) {
  return /* @__PURE__ */ o.jsxs("span", { className: "select-wrap", children: [
    /* @__PURE__ */ o.jsx("select", { value: u, "aria-label": c, onChange: a, children: g }),
    /* @__PURE__ */ o.jsx("svg", { className: "select-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ o.jsx("path", { d: "m6 9 6 6 6-6" }) })
  ] });
}
function qf({ examples: u, selected: a, onSelect: c }) {
  return u.length ? /* @__PURE__ */ o.jsxs("div", { className: "examples", children: [
    /* @__PURE__ */ o.jsx("span", { children: "Try an example" }),
    /* @__PURE__ */ o.jsx("div", { className: "example-list", children: u.map((g) => /* @__PURE__ */ o.jsx("button", { type: "button", disabled: !!g.disabledReason, title: g.disabledReason ?? g.description, className: a === g.id ? "selected" : "", onClick: () => c(g), children: g.label }, g.id)) })
  ] }) : null;
}
function Hf(u, a) {
  const c = u == null ? void 0 : u.status, g = u != null && u.runId ? a.find((x) => x.id === u.runId) : void 0, w = `${(g == null ? void 0 : g.origin) ?? ""} ${(g == null ? void 0 : g.mode) ?? ""} ${(g == null ? void 0 : g.task) ?? ""}`;
  return c === "running" ? /answerability/i.test(w) ? { label: "Checking answerability…", detail: "Judging whether the question is answerable from the context." } : /generat|quickPrompt/i.test(w) ? { label: "Generating…", detail: "The model is drafting an answer, then SIRIN scores it against the context." } : { label: "Scoring…", detail: "Running the detector over the answer." } : c === "queued" ? { label: "Queued…", detail: "Waiting for the runtime to pick up this run." } : { label: "Working…", detail: "The result will appear here when the operation finishes." };
}
function Xl({ activity: u, runs: a = [] }) {
  const { label: c, detail: g } = Hf(u, a);
  return /* @__PURE__ */ o.jsxs("section", { className: "result-card activity-card", "aria-live": "polite", "aria-busy": "true", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "activity-status", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Working" }),
      /* @__PURE__ */ o.jsx("h2", { children: c }),
      /* @__PURE__ */ o.jsx("p", { children: g })
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "skeleton-lines", "aria-hidden": "true", children: [
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {}),
      /* @__PURE__ */ o.jsx("i", {})
    ] })
  ] });
}
function Af({ answer: u, onComplete: a }) {
  const c = ue.useRef(a);
  c.current = a;
  const [g, w] = ue.useState("");
  return ue.useEffect(() => {
    w("");
    const x = u.match(/\S+\s*/g) ?? [u];
    let z = 0;
    const L = globalThis.setInterval(() => {
      z += 1, w(x.slice(0, z).join("")), z >= x.length && (globalThis.clearInterval(L), c.current());
    }, Math.max(24, Math.min(70, 900 / Math.max(x.length, 1))));
    return () => globalThis.clearInterval(L);
  }, [u]), /* @__PURE__ */ o.jsxs("p", { className: "answer-copy", children: [
    g,
    /* @__PURE__ */ o.jsx("span", { className: g.length < u.length ? "caret" : "caret hidden", "aria-hidden": "true" })
  ] });
}
function Bf({ answer: u, result: a }) {
  var z;
  if (!((z = a.segments) != null && z.length)) return /* @__PURE__ */ o.jsx("p", { className: "answer-copy", children: u || "No answer was returned." });
  const c = Ie(a.threshold), g = a.segments.map((L) => {
    const E = Ie(L.score);
    return Bl(E, L.verdict, c) ? E ?? 1 : -1;
  }), w = g.indexOf(Math.max(...g));
  let x = 0;
  return /* @__PURE__ */ o.jsx("p", { className: "answer-copy segmented", children: a.segments.map((L, E) => {
    const k = Ie(L.score), U = Bl(k, L.verdict, c), B = L.startCodePoint !== void 0 ? `characters ${L.startCodePoint}–${L.endCodePoint}` : "text segment", J = [B, k !== null ? `score ${k.toFixed(2)}` : null, c !== null ? `τ ${c.toFixed(3)}` : null, "probe confidence, not calibrated"].filter(Boolean).join(" · ");
    if (U) {
      const ie = k !== null ? fc(k, c) : 1, ve = Rr("--span-line-low", "--span-line-high", ie), K = { "--seg-wash": Rr("--span-wash-low", "--span-wash-high", ie), "--seg-line": ve, borderBottomWidth: ie >= 0.5 ? "3px" : "2px", "--d": `${ac + x * cc}ms` }, X = E === w ? "evidence graded is-peak" : "evidence graded";
      return x += 1, /* @__PURE__ */ o.jsxs("span", { className: X, style: K, tabIndex: 0, "aria-label": `${L.text}, ${J}`, title: J, children: [
        L.text,
        k !== null && /* @__PURE__ */ o.jsx("sup", { className: "evidence-badge", children: dc(k) })
      ] }, `${B}-${E}`);
    }
    return k !== null ? /* @__PURE__ */ o.jsx("span", { className: "evidence below", title: J, children: L.text }, `${B}-${E}`) : /* @__PURE__ */ o.jsx("span", { className: "evidence", children: L.text }, `${B}-${E}`);
  }) });
}
function Xf({ chunks: u, semantics: a }) {
  if (!u || u.length < 2) return null;
  const c = u.map((z) => Ie(z.score)).filter((z) => z !== null);
  if (!c.length) return null;
  const g = Math.min(...c), w = Math.max(...c) - g, x = Go(a) ?? "relative within this answer";
  return /* @__PURE__ */ o.jsxs("div", { className: "context-heatbar", role: "group", "aria-label": "Per-chunk context scores", children: [
    /* @__PURE__ */ o.jsx("span", { className: "context-heatbar-title", children: "Context chunks" }),
    /* @__PURE__ */ o.jsx("div", { className: "context-heatbar-cells", children: u.map((z, L) => {
      const E = Ie(z.score), k = E === null || w <= 0 ? 0.5 : Qo((E - g) / w), U = `Chunk ${(Ie(z.index) ?? L) + 1} of ${u.length}${E !== null ? ` · score ${E.toFixed(2)}` : ""} · ${x}`;
      return /* @__PURE__ */ o.jsx("span", { className: "context-heatbar-cell", style: { "--seg-wash": Rr("--span-wash-low", "--span-wash-high", k), "--seg-line": Rr("--span-line-low", "--span-line-high", k) }, tabIndex: 0, title: U, "aria-label": U }, L);
    }) })
  ] });
}
function Zf({ result: u }) {
  const a = Ie(u.threshold), c = (u.segments ?? []).filter((L) => Bl(Ie(L.score), L.verdict, a)), g = c.map((L) => Ie(L.score)).filter((L) => L !== null), w = g.length ? Math.max(...g) : null, x = c.length ? Rr("--span-line-low", "--span-line-high", w !== null ? fc(w, a) : 1) : "var(--span-safe)", z = c.length ? `${c.length} suspect ${c.length === 1 ? "span" : "spans"}${w !== null ? ` · max risk ${w.toFixed(2)}` : ""}` : "No spans above threshold";
  return /* @__PURE__ */ o.jsxs("div", { className: "span-footer", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "span-verdict", children: [
      /* @__PURE__ */ o.jsx("span", { className: "span-verdict-dot", style: { background: x }, "aria-hidden": "true" }),
      z
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "span-legend", children: [
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-word", children: "risk" }),
      a !== null && /* @__PURE__ */ o.jsxs("span", { className: "span-legend-num", children: [
        "τ ",
        a.toFixed(2)
      ] }),
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-bar", "aria-hidden": "true" }),
      /* @__PURE__ */ o.jsx("span", { className: "span-legend-num", children: "1.00" })
    ] })
  ] });
}
function Jf({ result: u }) {
  var w, x, z, L, E;
  const a = (w = u.spans) != null && w.length ? u.spans : (u.segments ?? []).filter((k) => k.verdict === !0).map((k) => ({ text: k.text, startCodePoint: k.startCodePoint, endCodePoint: k.endCodePoint, score: k.score, scoreKind: u.scoreSemantics, verdict: "suspect" })), c = u.categories ?? (Array.isArray(u.classes) ? u.classes : Object.entries(u.classes ?? {}).map(([k, U]) => ({ label: k, score: U })));
  return !(a.length || (x = u.claims) != null && x.length || c.length || u.rationale || (z = u.values) != null && z.length) ? null : /* @__PURE__ */ o.jsxs("details", { className: "evidence-details", children: [
    /* @__PURE__ */ o.jsx("summary", { children: "Evidence details" }),
    a.length ? /* @__PURE__ */ o.jsx("div", { className: "evidence-list", "aria-label": "Suspect spans", children: a.map((k, U) => /* @__PURE__ */ o.jsxs("article", { children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.text }),
        /* @__PURE__ */ o.jsx("small", { children: k.startCodePoint !== void 0 ? `Characters ${k.startCodePoint}–${k.endCodePoint}` : "Span evidence" })
      ] }),
      /* @__PURE__ */ o.jsxs("span", { children: [
        Ie(k.score) !== null ? dc(Ie(k.score)) : Er(k.score, k.scoreKind),
        " · ",
        k.verdict ?? "scored"
      ] })
    ] }, `${k.startCodePoint}-${U}`)) }) : null,
    (L = u.claims) != null && L.length ? /* @__PURE__ */ o.jsx("div", { className: "claim-list", children: u.claims.map((k, U) => /* @__PURE__ */ o.jsxs("article", { className: Jl(k.verdict), children: [
      /* @__PURE__ */ o.jsx(pc, { status: k.supported === !0 ? "safe" : k.supported === !1 ? "risk" : k.verdict }),
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.text ?? k.claim ?? `Claim ${U + 1}` }),
        k.rationale && /* @__PURE__ */ o.jsx("p", { children: k.rationale })
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: k.verdict ?? Er(k.score) })
    ] }, U)) }) : null,
    c.length ? /* @__PURE__ */ o.jsx("div", { className: "class-list", "aria-label": "Class scores", children: c.map((k) => /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("span", { children: In(k.label) }),
      /* @__PURE__ */ o.jsx("i", { children: /* @__PURE__ */ o.jsx("b", { style: { width: `${Math.max(0, Math.min(100, k.score * 100))}%` } }) }),
      /* @__PURE__ */ o.jsx("strong", { children: Er(k.score, "categorical_probabilities") })
    ] }, k.label)) }) : null,
    (E = u.values) != null && E.length ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx("div", { className: "mini-bars", "aria-hidden": "true", children: u.values.map((k, U) => /* @__PURE__ */ o.jsx("i", { style: { height: `${10 + Math.max(0, Math.min(1, k)) * 54}px` } }, U)) }),
      /* @__PURE__ */ o.jsx("ol", { className: "sr-only", "aria-label": "Relative token scores", children: u.values.map((k, U) => /* @__PURE__ */ o.jsxs("li", { children: [
        "Item ",
        U + 1,
        ": ",
        k.toFixed(3)
      ] }, U)) })
    ] }) : null,
    (u.rationale || u.note) && /* @__PURE__ */ o.jsx("p", { className: "rationale", children: u.rationale ?? u.note })
  ] });
}
function Kf({ run: u }) {
  const a = u.provenance ?? {}, c = u.origin === uc, g = c && typeof a.integritySha256 == "string" ? a.integritySha256 : null, w = Object.entries(a).filter(([x, z]) => x !== (g ? "integritySha256" : "") && (typeof z == "string" || typeof z == "number" || typeof z == "boolean"));
  return /* @__PURE__ */ o.jsxs("div", { className: "provenance", children: [
    /* @__PURE__ */ o.jsx("span", { children: c ? "Recorded result · verified" : In(u.origin ?? u.mode ?? "live run") }),
    (u.setupSnapshot ?? u.setup) && /* @__PURE__ */ o.jsx("span", { children: Hl(u.setupSnapshot ?? u.setup, "detectorPreset", "detectorLabel") }),
    u.staleSetup && /* @__PURE__ */ o.jsx("span", { className: "warning", children: "Different setup" }),
    u.sourceRunId && /* @__PURE__ */ o.jsxs("span", { children: [
      "Source ",
      u.sourceRunId
    ] }),
    g && /* @__PURE__ */ o.jsxs("span", { title: g, children: [
      "Checkpoint ",
      g.slice(0, 12),
      "…"
    ] }),
    w.slice(0, 3).map(([x, z]) => /* @__PURE__ */ o.jsxs("span", { children: [
      In(x),
      ": ",
      String(z)
    ] }, x))
  ] });
}
function Qf({ timings: u }) {
  if (!u) return null;
  const c = [["generation", u.generationSeconds], ["detection", u.detectionSeconds], ["total", u.totalSeconds]].map(([g, w]) => [g, Ie(w)]).filter(([, g]) => g !== null);
  return c.length ? /* @__PURE__ */ o.jsx("div", { className: "latency-strip", "aria-label": "Run latency", children: c.map(([g, w], x) => /* @__PURE__ */ o.jsxs("span", { children: [
    x > 0 ? "· " : "",
    g,
    " ",
    /* @__PURE__ */ o.jsxs("b", { children: [
      w.toFixed(1),
      "s"
    ] })
  ] }, g)) }) : null;
}
function Zl({ run: u, motion: a, onAction: c, onPrepareRerun: g }) {
  var Ze, We, Je, ze, V;
  const w = u.analysis ?? u.result ?? {}, x = w.scoreSemantics ?? u.scoreSemantics, z = w.score ?? w.confidence ?? u.score, L = Go(x, w.scaleLabel ?? u.scaleLabel), E = (w.segments ?? []).some((_) => Ie(_.score) !== null || _.verdict === !0), k = w.verdict ?? u.verdict, U = w.label ?? (typeof k == "string" ? k : null) ?? (u.status === "failed" ? "Failed" : "Result"), B = u.origin === uc, J = !B && /replay|recorded/i.test(`${u.origin ?? ""} ${u.mode ?? ""}`), ie = ((Ze = globalThis.matchMedia) == null ? void 0 : Ze.call(globalThis, "(prefers-reduced-motion: reduce)").matches) ?? !1, [ve] = ue.useState(() => {
    const _ = !rc.has(u.id);
    return rc.add(u.id), _;
  }), K = a !== "static" && !ie && ve, X = J && K, [b, Ne] = ue.useState(!X), ge = Ie(w.threshold), fe = (w.segments ?? []).filter((_) => Bl(Ie(_.score), _.verdict, ge)).length, Te = E && K, ke = ac + fe * cc + Wf, pe = typeof u.error == "string" ? u.error : (We = u.error) == null ? void 0 : We.message, Q = u.error && typeof u.error == "object" ? u.error : null;
  return /* @__PURE__ */ o.jsxs("section", { className: `result-card ${Jl(k ?? U)}${Te ? " is-reveal" : ""}`, style: Te ? { "--reveal-total": `${ke}ms` } : void 0, "aria-live": "polite", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "result-heading", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Outcome" }),
        /* @__PURE__ */ o.jsx("h2", { children: U }),
        /* @__PURE__ */ o.jsx("p", { children: w.summary ?? (u.status === "partial" ? "The answer was preserved, but part of analysis did not complete." : "Evidence is shown in the answer and details below.") })
      ] }),
      !E && Ie(z) !== null && L && /* @__PURE__ */ o.jsxs("div", { className: "score-orb", children: [
        /* @__PURE__ */ o.jsx("strong", { children: Er(z, x) }),
        /* @__PURE__ */ o.jsx("span", { children: L }),
        ["thresholded_raw_score", "thresholdedRawScore"].includes(x ?? "") && ge !== null && /* @__PURE__ */ o.jsxs("small", { className: "decision-band", children: [
          "vs τ ",
          ge.toFixed(2)
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsxs("div", { className: "answer-block", children: [
      /* @__PURE__ */ o.jsxs("div", { className: "answer-label", children: [
        /* @__PURE__ */ o.jsx("span", { children: "Answer" }),
        /* @__PURE__ */ o.jsx("small", { children: B ? Of.recordedResultVerified : J ? "Recorded answer · live detection" : u.origin === "importedSnapshot" || u.origin === "imported" ? "Imported snapshot" : /answerability/i.test(u.origin ?? u.mode ?? "") ? "Answerability · live detection" : /supplied/i.test(u.origin ?? u.mode ?? "") ? "Supplied answer · live detection" : "Generated now" })
      ] }),
      !E && (((Je = w.contextChunkScores) == null ? void 0 : Je.length) ?? 0) > 1 && /* @__PURE__ */ o.jsx(Xf, { chunks: w.contextChunkScores, semantics: x }),
      X && !b ? /* @__PURE__ */ o.jsx(Af, { answer: u.answer ?? "", onComplete: () => Ne(!0) }) : /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
        /* @__PURE__ */ o.jsx(Bf, { answer: u.answer ?? "", result: w }),
        E && /* @__PURE__ */ o.jsx(Zf, { result: w })
      ] })
    ] }),
    w.unavailableReason && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice warning", children: [
      /* @__PURE__ */ o.jsx("b", { children: "Analysis unavailable" }),
      /* @__PURE__ */ o.jsx("span", { children: w.unavailableReason })
    ] }),
    pe && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice error", children: [
      /* @__PURE__ */ o.jsx("b", { children: u.status === "partial" ? "Detection did not finish" : "Run failed" }),
      /* @__PURE__ */ o.jsx("span", { children: pe }),
      (Q == null ? void 0 : Q.correlationId) && !Df.has(Q.code ?? "") && /* @__PURE__ */ o.jsxs("small", { children: [
        "Reference ",
        Q.correlationId
      ] })
    ] }),
    (ze = u.warnings) == null ? void 0 : ze.map((_, Le) => /* @__PURE__ */ o.jsx("div", { className: "inline-notice warning", children: _ }, Le)),
    /* @__PURE__ */ o.jsx(Jf, { result: w }),
    /* @__PURE__ */ o.jsx(Kf, { run: u }),
    /* @__PURE__ */ o.jsx(Qf, { timings: u.timings }),
    /* @__PURE__ */ o.jsxs("div", { className: "result-actions", children: [
      B && ((V = u.inputs) == null ? void 0 : V.exampleId) && /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", title: "Replays the verified answer and runs the probe live. Loads the model.", onClick: () => {
        var _, Le, Ce;
        return c("submit", { task: "faithfulness", mode: "recordedReplay", context: ((_ = u.inputs) == null ? void 0 : _.context) ?? "", question: ((Le = u.inputs) == null ? void 0 : Le.question) ?? "", suppliedAnswer: u.answer ?? "", prompt: "", exampleId: (Ce = u.inputs) == null ? void 0 : Ce.exampleId });
      }, children: [
        /* @__PURE__ */ o.jsx(Xe, { name: "spark" }),
        "Run it live"
      ] }),
      (u.status === "partial" || u.status === "failed") && u.answer && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", onClick: () => c("retryDetection", { runId: u.id }), children: "Retry detection" }),
      (u.origin === "importedSnapshot" || u.origin === "imported" || u.immutable) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", onClick: () => g(u), children: "Rerun with current setup" }),
      /* @__PURE__ */ o.jsxs("button", { type: "button", className: "quiet", onClick: () => c("exportRun", { runId: u.id }), children: [
        /* @__PURE__ */ o.jsx(Xe, { name: "download" }),
        "Export run"
      ] })
    ] })
  ] });
}
function Gf({ payload: u, draft: a, setDraft: c, busy: g, motion: w, onAction: x, onPrepareRerun: z, onCompare: L }) {
  var ze;
  const E = u.capabilities ?? {}, k = E, U = String(((ze = u.setup) == null ? void 0 : ze.task) ?? "faithfulness"), B = U === a.task ? !0 : { enabled: !1, reason: `The active detector supports ${Jo(U)}, not ${Jo(a.task)}.` }, J = a.task === "answerability" ? k.canAnswerability ?? B : B, ie = a.task === "faithfulness" && a.mode === "generate" ? E.canGenerate : !0, ve = a.prompt.trim().length > 0 || a.context.trim().length > 0 && a.question.trim().length > 0, K = Ue(J) && Ue(ie) && ve && (a.task === "answerability" || a.mode === "generate" || a.answer.trim().length > 0), X = u.availablePresets ?? [], b = u.replayTarget ?? null, [Ne, ge] = ue.useState(!1), [fe, Te] = ue.useState(""), ke = () => {
    const V = fe || X[0];
    !V || !K || g || L(V, {
      task: a.task,
      context: a.context,
      question: a.question,
      suppliedAnswer: a.mode === "supplied" ? a.answer : "",
      prompt: a.prompt,
      exampleId: a.exampleId
    });
  }, pe = u.examples ?? [], Q = pe.find((V) => V.id === a.exampleId), Ze = !!(Q && (Q.recordedAnswer || Q.answer)), We = (V) => c({
    task: V.task ?? a.task,
    mode: a.mode,
    exampleId: V.id,
    context: V.context ?? "",
    question: V.question ?? "",
    answer: V.answer ?? V.recordedAnswer ?? "",
    prompt: V.prompt ?? "",
    sourceRunId: null
  }, !0), Je = (V) => {
    if (V.preventDefault(), !K || g) return;
    const _ = a.task === "answerability" ? "answerability" : a.sourceRunId && a.prompt && !a.context && !a.question ? "quickPrompt" : a.mode === "generate" ? "generateAndScore" : "scoreSuppliedAnswer";
    x("submit", {
      task: a.task,
      mode: _,
      context: a.context,
      question: a.question,
      suppliedAnswer: a.mode === "supplied" ? a.answer : "",
      prompt: a.prompt,
      exampleId: a.exampleId,
      ...a.sourceRunId ? { sourceRunId: a.sourceRunId } : {}
    }), a.sourceRunId && c({ ...a, sourceRunId: null });
  };
  if (b) {
    const V = () => x("submit", { task: "faithfulness", mode: "recordedReplay", context: b.context, question: b.question, suppliedAnswer: b.answer, prompt: "", exampleId: b.exampleId });
    return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content analyze-workspace", children: [
      /* @__PURE__ */ o.jsxs("form", { className: "analysis-form", onSubmit: (_) => _.preventDefault(), children: [
        /* @__PURE__ */ o.jsxs("div", { className: "inline-notice info", children: [
          /* @__PURE__ */ o.jsx("b", { children: "Recorded result" }),
          /* @__PURE__ */ o.jsx("span", { children: "This detector needs local model weights the hosted demo doesn't ship, so it replays a verified recorded case. For live scoring, pick a Judge — API preset." })
        ] }),
        /* @__PURE__ */ o.jsx(kn, { label: "Context", hint: `${b.context.length.toLocaleString()} characters`, children: /* @__PURE__ */ o.jsx("textarea", { rows: 7, value: b.context, readOnly: !0 }) }),
        /* @__PURE__ */ o.jsx(kn, { label: "Question", children: /* @__PURE__ */ o.jsx("textarea", { rows: 2, value: b.question, readOnly: !0 }) }),
        /* @__PURE__ */ o.jsx(kn, { label: "Recorded answer", children: /* @__PURE__ */ o.jsx("textarea", { rows: 4, value: b.answer, readOnly: !0 }) }),
        /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
          /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: !0, title: "Live scoring is unavailable for this preset on the hosted demo — use Replay recorded answer.", children: [
            /* @__PURE__ */ o.jsx(Xe, { name: "spark" }),
            "Generate & score"
          ] }),
          /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: g, onClick: V, children: [
            /* @__PURE__ */ o.jsx(Xe, { name: "spark" }),
            "Replay recorded answer"
          ] })
        ] })
      ] }),
      g ? /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }) : u.selectedRun ? /* @__PURE__ */ o.jsx(Zl, { run: u.selectedRun, motion: w, onAction: x, onPrepareRerun: z }, u.selectedRun.id) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
        /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(Xe, { name: "spark" }) }),
        /* @__PURE__ */ o.jsx("h2", { children: "Your evidence map will appear here." }),
        /* @__PURE__ */ o.jsx("p", { children: "Replay the recorded answer to see this preset's graded result." })
      ] })
    ] });
  }
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content analyze-workspace", children: [
    /* @__PURE__ */ o.jsx(qf, { examples: pe.filter((V) => !V.task || V.task === a.task), selected: a.exampleId, onSelect: We }),
    /* @__PURE__ */ o.jsxs("form", { className: "analysis-form", onSubmit: Je, children: [
      /* @__PURE__ */ o.jsxs("div", { className: "form-row", children: [
        /* @__PURE__ */ o.jsx(kn, { label: "Task", children: /* @__PURE__ */ o.jsxs(Al, { value: a.task, onChange: (V) => {
          const _ = V.target.value;
          c({ ...a, task: _, mode: _ === "answerability" ? "generate" : a.mode }, !0);
        }, children: [
          /* @__PURE__ */ o.jsx("option", { value: "faithfulness", disabled: U !== "faithfulness", children: "Hallucination" }),
          /* @__PURE__ */ o.jsx("option", { value: "answerability", disabled: !Ue(k.canAnswerability ?? U === "answerability"), children: "Answerability" })
        ] }) }),
        a.task === "faithfulness" && /* @__PURE__ */ o.jsx(kn, { label: "Answer source", children: /* @__PURE__ */ o.jsxs(Al, { value: a.mode, onChange: (V) => c({ ...a, mode: V.target.value }, !0), children: [
          /* @__PURE__ */ o.jsx("option", { value: "generate", disabled: !Ue(E.canGenerate), children: "Generate an answer" }),
          /* @__PURE__ */ o.jsx("option", { value: "supplied", children: "Score supplied answer" })
        ] }) })
      ] }),
      a.prompt && /* @__PURE__ */ o.jsxs("details", { className: "prompt-disclosure", children: [
        /* @__PURE__ */ o.jsxs("summary", { children: [
          /* @__PURE__ */ o.jsx("svg", { className: "disclosure-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ o.jsx("path", { d: "m9 18 6-6-6-6" }) }),
          /* @__PURE__ */ o.jsx("span", { children: "Exact model prompt" }),
          /* @__PURE__ */ o.jsxs("span", { className: "disclosure-count", children: [
            a.prompt.length.toLocaleString(),
            " characters"
          ] })
        ] }),
        /* @__PURE__ */ o.jsx(kn, { label: "Prompt", children: /* @__PURE__ */ o.jsx("textarea", { rows: 5, value: a.prompt, placeholder: "Verified example or imported prompt…", onChange: (V) => c({ ...a, prompt: V.target.value, exampleId: null }), onBlur: () => c(a, !0) }) })
      ] }),
      /* @__PURE__ */ o.jsx(kn, { label: "Context", hint: `${a.context.length.toLocaleString()} characters`, children: /* @__PURE__ */ o.jsx("textarea", { rows: 7, value: a.context, placeholder: "Paste the source material the answer must stay grounded in…", onChange: (V) => c({ ...a, context: V.target.value }), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ o.jsx(kn, { label: "Question", children: /* @__PURE__ */ o.jsx("textarea", { rows: 2, value: a.question, placeholder: "What should the model answer from this context?", onChange: (V) => c({ ...a, question: V.target.value }), onBlur: () => c(a, !0) }) }),
      a.task === "faithfulness" && a.mode === "supplied" && /* @__PURE__ */ o.jsx(kn, { label: "Answer to score", children: /* @__PURE__ */ o.jsx("textarea", { rows: 4, value: a.answer, placeholder: "Paste the answer that should be checked…", onChange: (V) => c({ ...a, answer: V.target.value }), onBlur: () => c(a, !0) }) }),
      !Ue(J) && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: oc(J) ?? "The active detector does not support this task." }),
      !Ue(ie) && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: oc(ie) ?? "Generation is not available with the active setup." }),
      a.sourceRunId && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice info", children: [
        /* @__PURE__ */ o.jsx("b", { children: "Imported run prepared" }),
        /* @__PURE__ */ o.jsx("span", { children: "Review these inputs, then submit explicitly with the current setup." })
      ] }),
      /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
        /* @__PURE__ */ o.jsxs("button", { className: "primary", type: "submit", disabled: !K || g, children: [
          /* @__PURE__ */ o.jsx(Xe, { name: "spark" }),
          a.task === "answerability" ? "Check answerability" : a.mode === "supplied" ? "Score answer" : "Generate & score"
        ] }),
        Ze && /* @__PURE__ */ o.jsxs("button", { type: "button", className: "secondary", disabled: g, onClick: () => x("submit", { task: (Q == null ? void 0 : Q.task) ?? "faithfulness", mode: "recordedReplay", context: a.context, question: a.question, suppliedAnswer: (Q == null ? void 0 : Q.recordedAnswer) ?? (Q == null ? void 0 : Q.answer) ?? "", prompt: "", exampleId: Q == null ? void 0 : Q.id }), children: [
          /* @__PURE__ */ o.jsx(Xe, { name: "spark" }),
          "Replay recorded answer"
        ] }),
        X.length > 0 && /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", disabled: g, "aria-expanded": Ne, onClick: () => ge((V) => !V), children: "Compare detectors…" })
      ] }),
      Ne && X.length > 0 && /* @__PURE__ */ o.jsxs("div", { className: "compare-picker", children: [
        /* @__PURE__ */ o.jsx(kn, { label: "Second detector (B)", hint: "scores the same answer", children: /* @__PURE__ */ o.jsx(Al, { ariaLabel: "Second detector for comparison", value: fe || X[0], onChange: (V) => Te(V.target.value), children: X.map((V) => /* @__PURE__ */ o.jsx("option", { value: V, children: V }, V)) }) }),
        /* @__PURE__ */ o.jsxs("button", { type: "button", className: "primary", disabled: !K || g, onClick: ke, children: [
          /* @__PURE__ */ o.jsx(Xe, { name: "spark" }),
          "Run comparison"
        ] }),
        !K && /* @__PURE__ */ o.jsx("p", { className: "field-error", children: "Enter a context and question (or an answer to score) first." })
      ] })
    ] }),
    g ? /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }) : u.selectedRun ? /* @__PURE__ */ o.jsx(Zl, { run: u.selectedRun, motion: w, onAction: x, onPrepareRerun: z }, u.selectedRun.id) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
      /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(Xe, { name: "spark" }) }),
      /* @__PURE__ */ o.jsx("h2", { children: "Your evidence map will appear here." }),
      /* @__PURE__ */ o.jsx("p", { children: "Results lead with the outcome, then reveal only the detail each detector can honestly support." })
    ] })
  ] });
}
function Yf({ agreement: u }) {
  const a = [
    { key: "both", label: "Both flag", count: u.both, color: "var(--span-line-high)" },
    { key: "aOnly", label: "A only", count: u.aOnly, color: "var(--span-line-low)" },
    { key: "bOnly", label: "B only", count: u.bOnly, color: "var(--brand)" },
    { key: "neither", label: "Neither", count: u.neither, color: "var(--safe)" }
  ], c = a.reduce((x, z) => x + z.count, 0), g = c || 1, w = (x) => Math.round(x / g * 100);
  return /* @__PURE__ */ o.jsxs("div", { className: "agreement", children: [
    /* @__PURE__ */ o.jsxs("p", { className: "eyebrow", children: [
      "Localization agreement · ",
      c,
      " characters"
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "agreement-bar", role: "img", "aria-label": a.map((x) => `${x.label} ${x.count}`).join(", "), children: a.map((x) => x.count > 0 ? /* @__PURE__ */ o.jsx("span", { style: { width: `${x.count / g * 100}%`, background: x.color }, title: `${x.label}: ${x.count} (${w(x.count)}%)` }, x.key) : null) }),
    /* @__PURE__ */ o.jsx("div", { className: "agreement-legend", children: a.map((x) => /* @__PURE__ */ o.jsxs("span", { children: [
      /* @__PURE__ */ o.jsx("i", { style: { background: x.color }, "aria-hidden": "true" }),
      x.label,
      " ",
      /* @__PURE__ */ o.jsx("b", { children: x.count }),
      " ",
      /* @__PURE__ */ o.jsxs("em", { children: [
        w(x.count),
        "%"
      ] })
    ] }, x.key)) })
  ] });
}
function bf({ compare: u }) {
  const a = Ie(u.deltaScore);
  return /* @__PURE__ */ o.jsxs("section", { className: "compare-verdict", children: [
    u.agreement ? /* @__PURE__ */ o.jsx(Yf, { agreement: u.agreement }) : /* @__PURE__ */ o.jsxs("div", { className: "compare-note", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Localization agreement" }),
      /* @__PURE__ */ o.jsx("p", { children: u.agreementNote ?? "No per-character overlap is available for these detectors." })
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "compare-delta", children: a !== null ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsxs("span", { className: "compare-delta-value", children: [
        a > 0 ? "+" : "",
        a.toFixed(2)
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: u.deltaNote })
    ] }) : /* @__PURE__ */ o.jsx("span", { className: "compare-note-line", children: u.deltaNote || "Different score scales — localization overlap only." }) })
  ] });
}
function sc({ label: u, preset: a, run: c, motion: g, onAction: w, onPrepareRerun: x }) {
  var k, U;
  const z = ((k = c == null ? void 0 : c.analysis) == null ? void 0 : k.scoreSemantics) ?? ((U = c == null ? void 0 : c.setupSnapshot) == null ? void 0 : U.scoreSemantics), L = Go(z), E = c ? ["queued", "running"].includes(c.status) : !1;
  return /* @__PURE__ */ o.jsxs("section", { className: "compare-column", children: [
    /* @__PURE__ */ o.jsxs("header", { className: "compare-col-head", children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: u }),
      /* @__PURE__ */ o.jsx("h3", { children: a ?? "Detector" }),
      L && /* @__PURE__ */ o.jsx("small", { children: L })
    ] }),
    c ? E ? /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
      /* @__PURE__ */ o.jsx("h2", { children: "Scoring…" }),
      /* @__PURE__ */ o.jsx("p", { children: "Running this detector over the shared answer." })
    ] }) : /* @__PURE__ */ o.jsx(Zl, { run: c, motion: g, onAction: w, onPrepareRerun: x }, c.id) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
      /* @__PURE__ */ o.jsx("h2", { children: "Waiting…" }),
      /* @__PURE__ */ o.jsx("p", { children: "This side scores the same answer once it is available." })
    ] })
  ] });
}
function _f({ payload: u, motion: a, onAction: c, onPrepareRerun: g, onBack: w }) {
  const x = u.compare;
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content compare-workspace", children: [
    /* @__PURE__ */ o.jsx("div", { className: "compare-head", children: /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", onClick: w, children: "← Back to Analyze" }) }),
    x ? /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
      /* @__PURE__ */ o.jsx(bf, { compare: x }),
      /* @__PURE__ */ o.jsxs("div", { className: "compare-grid", children: [
        /* @__PURE__ */ o.jsx(sc, { label: "Detector A", preset: x.presetA, run: x.runA, motion: a, onAction: c, onPrepareRerun: g }),
        /* @__PURE__ */ o.jsx(sc, { label: "Detector B", preset: x.presetB, run: x.runB, motion: a, onAction: c, onPrepareRerun: g })
      ] })
    ] }) : /* @__PURE__ */ o.jsxs("section", { className: "result-placeholder", children: [
      /* @__PURE__ */ o.jsx("div", { children: /* @__PURE__ */ o.jsx(Xe, { name: "spark" }) }),
      /* @__PURE__ */ o.jsx("h2", { children: "No comparison yet." }),
      /* @__PURE__ */ o.jsx("p", { children: "Open “Compare detectors…” in Analyze to score one answer with two detectors side by side." })
    ] })
  ] });
}
function $f(u) {
  if (!u) return "Time unavailable";
  const a = new Date(u);
  return Number.isNaN(a.valueOf()) ? u : new Intl.DateTimeFormat(void 0, { dateStyle: "medium", timeStyle: "short" }).format(a);
}
function ep({ runs: u, selectedId: a, onSelect: c, onAnalyze: g }) {
  const [w, x] = ue.useState(""), [z, L] = ue.useState("all"), E = u.filter((k) => (z === "all" || k.status === z) && `${k.title ?? ""} ${k.question ?? ""} ${k.prompt ?? ""} ${k.answer ?? ""}`.toLowerCase().includes(w.toLowerCase()));
  return /* @__PURE__ */ o.jsxs("section", { className: "run-browser", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "section-heading", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "History" }),
        /* @__PURE__ */ o.jsxs("h2", { children: [
          u.length,
          " ",
          u.length === 1 ? "run" : "runs"
        ] })
      ] }),
      /* @__PURE__ */ o.jsxs("div", { className: "filters", children: [
        /* @__PURE__ */ o.jsx("input", { type: "search", "aria-label": "Search runs", value: w, placeholder: "Search runs", onChange: (k) => x(k.target.value) }),
        /* @__PURE__ */ o.jsxs(Al, { ariaLabel: "Filter runs by status", value: z, onChange: (k) => L(k.target.value), children: [
          /* @__PURE__ */ o.jsx("option", { value: "all", children: "All outcomes" }),
          /* @__PURE__ */ o.jsx("option", { value: "succeeded", children: "Succeeded" }),
          /* @__PURE__ */ o.jsx("option", { value: "partial", children: "Partial" }),
          /* @__PURE__ */ o.jsx("option", { value: "failed", children: "Failed" }),
          /* @__PURE__ */ o.jsx("option", { value: "interrupted", children: "Interrupted" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ o.jsx("div", { className: "run-list", children: E.length ? E.map((k) => /* @__PURE__ */ o.jsxs("button", { type: "button", className: a === k.id ? "selected" : "", onClick: () => c(k), children: [
      /* @__PURE__ */ o.jsx(pc, { status: k.status }),
      /* @__PURE__ */ o.jsxs("span", { children: [
        /* @__PURE__ */ o.jsx("b", { children: k.title ?? k.question ?? k.prompt ?? `Run ${k.id}` }),
        /* @__PURE__ */ o.jsxs("small", { children: [
          $f(k.completedAt ?? k.createdAt),
          " · ",
          Jo(k.task),
          " · ",
          In(k.status)
        ] })
      ] }),
      /* @__PURE__ */ o.jsx("strong", { children: typeof k.verdict == "boolean" ? k.task === "answerability" ? k.verdict ? "Answerable" : "Unanswerable" : k.verdict ? "Unsupported" : "Supported" : k.verdict ?? Er(k.score, k.scoreSemantics) }),
      /* @__PURE__ */ o.jsx(Xe, { name: "arrow" })
    ] }, k.id)) : u.length === 0 ? /* @__PURE__ */ o.jsxs("div", { className: "empty-list", children: [
      "No runs yet — ",
      /* @__PURE__ */ o.jsx("button", { type: "button", className: "empty-link", onClick: g, children: "analyze a case" }),
      " to get started."
    ] }) : /* @__PURE__ */ o.jsx("div", { className: "empty-list", children: "No runs match these filters." }) })
  ] });
}
function np({ disabled: u, onImport: a }) {
  const c = ue.useRef(null), [g, w] = ue.useState(""), x = async (z) => {
    if (z) {
      if (z.size > 10 * 1024 * 1024) {
        w("Portable bundles must be 10 MiB or smaller.");
        return;
      }
      w(""), a(await z.text(), z.name), c.current && (c.current.value = "");
    }
  };
  return /* @__PURE__ */ o.jsxs(o.Fragment, { children: [
    /* @__PURE__ */ o.jsx("input", { ref: c, hidden: !0, type: "file", accept: "application/json,.json", onChange: (z) => {
      var L;
      return void x((L = z.target.files) == null ? void 0 : L[0]);
    } }),
    /* @__PURE__ */ o.jsxs("button", { type: "button", className: "secondary", disabled: u, onClick: () => {
      var z;
      return (z = c.current) == null ? void 0 : z.click();
    }, children: [
      /* @__PURE__ */ o.jsx(Xe, { name: "upload" }),
      "Import JSON"
    ] }),
    g && /* @__PURE__ */ o.jsx("span", { className: "field-error", role: "alert", children: g })
  ] });
}
function tp({ payload: u, quickPrompt: a, setQuickPrompt: c, selectedId: g, setSelectedId: w, busy: x, motion: z, onAction: L, onPrepareRerun: E, onAnalyze: k }) {
  var ie, ve, K, X;
  const U = u.runs ?? [], B = u.selectedRun ?? U.find((b) => b.id === g) ?? null, J = String(((ie = u.setup) == null ? void 0 : ie.task) ?? "faithfulness") === "faithfulness";
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content runs-workspace", children: [
    /* @__PURE__ */ o.jsxs("form", { className: "quick-run", onSubmit: (b) => {
      b.preventDefault(), a.trim() && !x && J && L("submit", { task: "faithfulness", mode: "quickPrompt", context: "", question: "", suppliedAnswer: "", prompt: a, exampleId: null });
    }, children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Quick run" }),
        /* @__PURE__ */ o.jsx("h2", { children: "Ask without building a thread." }),
        /* @__PURE__ */ o.jsx("p", { children: "Each prompt becomes an independent, auditable run." })
      ] }),
      /* @__PURE__ */ o.jsx(kn, { label: "Prompt", children: /* @__PURE__ */ o.jsx("textarea", { rows: 3, value: a, placeholder: "Ask the active generator…", onChange: (b) => c(b.target.value), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ o.jsxs("div", { className: "form-actions", children: [
        /* @__PURE__ */ o.jsxs("button", { type: "submit", className: "primary", title: J ? void 0 : "Quick Run requires a hallucination detector.", disabled: !a.trim() || x || !Ue((ve = u.capabilities) == null ? void 0 : ve.canGenerate) || !J, children: [
          /* @__PURE__ */ o.jsx(Xe, { name: "spark" }),
          "Run prompt"
        ] }),
        /* @__PURE__ */ o.jsx(np, { disabled: !Ue((K = u.capabilities) == null ? void 0 : K.canImport), onImport: (b) => L("import", { json: b }) }),
        /* @__PURE__ */ o.jsxs("button", { type: "button", className: "quiet", disabled: !U.length || !Ue((X = u.capabilities) == null ? void 0 : X.canExport), onClick: () => L("exportBundle", {}), children: [
          /* @__PURE__ */ o.jsx(Xe, { name: "download" }),
          "Export session"
        ] })
      ] })
    ] }),
    x && /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }),
    /* @__PURE__ */ o.jsxs("div", { className: "runs-grid", children: [
      /* @__PURE__ */ o.jsx(ep, { runs: U, selectedId: (B == null ? void 0 : B.id) ?? g, onSelect: (b) => {
        w(b.id), L("selectRun", { runId: b.id });
      }, onAnalyze: k }),
      /* @__PURE__ */ o.jsx("aside", { className: "run-detail", children: B ? /* @__PURE__ */ o.jsx(Zl, { run: B, motion: z, onAction: L, onPrepareRerun: E }, B.id) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
        /* @__PURE__ */ o.jsx("h2", { children: "Select a run" }),
        /* @__PURE__ */ o.jsx("p", { children: "Its outcome, evidence, and provenance will appear here." })
      ] }) })
    ] })
  ] });
}
function rp(u) {
  return u ? Array.isArray(u) ? u : Object.entries(u).map(([a, c]) => ({ label: In(a), value: typeof c == "object" ? JSON.stringify(c) : c })) : [];
}
function lp({ diagnostics: u }) {
  var c;
  const a = u == null ? void 0 : u.attention;
  return (c = a == null ? void 0 : a.values) != null && c.length ? /* @__PURE__ */ o.jsxs("section", { className: "attention-card", children: [
    /* @__PURE__ */ o.jsx("div", { className: "section-heading", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Attention" }),
      /* @__PURE__ */ o.jsx("h2", { children: a.title ?? "Bounded attention summary" })
    ] }) }),
    /* @__PURE__ */ o.jsx("div", { className: "table-scroll", children: /* @__PURE__ */ o.jsxs("table", { children: [
      /* @__PURE__ */ o.jsx("thead", { children: /* @__PURE__ */ o.jsxs("tr", { children: [
        /* @__PURE__ */ o.jsx("th", { children: "Token" }),
        (a.columnLabels ?? []).map((g) => /* @__PURE__ */ o.jsx("th", { children: g }, g))
      ] }) }),
      /* @__PURE__ */ o.jsx("tbody", { children: a.values.map((g, w) => {
        var x;
        return /* @__PURE__ */ o.jsxs("tr", { children: [
          /* @__PURE__ */ o.jsx("th", { children: ((x = a.rowLabels) == null ? void 0 : x[w]) ?? w + 1 }),
          g.map((z, L) => /* @__PURE__ */ o.jsx("td", { style: z === null ? void 0 : { "--attention": String(Math.max(0, Math.min(1, z))) }, children: /* @__PURE__ */ o.jsx("span", { children: z === null ? "—" : z.toFixed(2) }) }, L))
        ] }, w);
      }) })
    ] }) }),
    a.note && /* @__PURE__ */ o.jsx("p", { className: "caption", children: a.note })
  ] }) : /* @__PURE__ */ o.jsxs("div", { className: "result-placeholder compact", children: [
    /* @__PURE__ */ o.jsx("h2", { children: "No attention summary yet" }),
    /* @__PURE__ */ o.jsx("p", { children: "Attention summaries appear here when the active detector captures them." })
  ] });
}
function ip({ recipe: u }) {
  const [a, c] = ue.useState(!1), g = () => {
    var w, x;
    (x = (w = globalThis.navigator) == null ? void 0 : w.clipboard) == null || x.writeText(u.code).then(
      () => {
        c(!0), globalThis.setTimeout(() => c(!1), 1500);
      },
      () => {
      }
    );
  };
  return /* @__PURE__ */ o.jsxs("article", { className: "recipe-card", children: [
    /* @__PURE__ */ o.jsxs("div", { className: "recipe-head", children: [
      /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("h3", { children: u.title }),
        /* @__PURE__ */ o.jsx("p", { children: u.description })
      ] }),
      /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", onClick: g, "aria-label": `Copy the ${u.title} snippet`, children: a ? "Copied" : "Copy" })
    ] }),
    u.reference && /* @__PURE__ */ o.jsxs("p", { className: "recipe-reference", children: [
      "Reference: ",
      /* @__PURE__ */ o.jsx("code", { children: u.reference })
    ] }),
    /* @__PURE__ */ o.jsx("pre", { className: "recipe-code", children: /* @__PURE__ */ o.jsx("code", { children: u.code }) })
  ] });
}
function op({ recipes: u }) {
  return u.length ? /* @__PURE__ */ o.jsxs("section", { className: "recipes-section", children: [
    /* @__PURE__ */ o.jsx("div", { className: "section-heading", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("p", { className: "eyebrow", children: "Extend" }),
      /* @__PURE__ */ o.jsx("h2", { children: "Add a detector" }),
      /* @__PURE__ */ o.jsx("p", { children: "Copy-paste starting points — each snippet is real SIRIN API you can adapt." })
    ] }) }),
    /* @__PURE__ */ o.jsx("div", { className: "recipe-list", children: u.map((a) => /* @__PURE__ */ o.jsx(ip, { recipe: a }, a.id)) })
  ] }) : null;
}
function sp({ payload: u, busy: a, onAction: c }) {
  var L;
  const g = u.diagnostics, w = u.capabilities ?? {}, x = g != null && g.metrics ? rp(g.metrics) : [
    { label: "Runtime", value: (g == null ? void 0 : g.runtime) ?? "Python" },
    { label: "Device", value: (g == null ? void 0 : g.device) ?? "Loads on first run" },
    { label: "Model", value: (g == null ? void 0 : g.activeModel) ?? (g != null && g.modelLoaded ? "Loaded" : "Loads on first run") },
    { label: "Attention", value: g != null && g.attentionAvailable ? "Available" : "Not captured in this mode" }
  ], z = !!((L = u.capabilities) != null && L.trustedLocal);
  return /* @__PURE__ */ o.jsxs("main", { className: "workspace-content diagnostics-workspace", children: [
    !z && /* @__PURE__ */ o.jsx("div", { className: "privacy-banner", children: /* @__PURE__ */ o.jsxs("div", { children: [
      /* @__PURE__ */ o.jsx("b", { children: "Shared-safe diagnostics" }),
      /* @__PURE__ */ o.jsx("span", { children: "Sensitive paths, traces, provider responses, and raw runtime errors remain hidden." })
    ] }) }),
    a && /* @__PURE__ */ o.jsx(Xl, { activity: u.activity, runs: u.runs ?? [] }),
    z && (Ue(w.canRefreshDiagnostics, !1) || Ue(w.canOpenCachedAttention, !1) || Ue(w.canOpenLiveAttention, !1) || Ue(w.canUnloadModels, !1)) && /* @__PURE__ */ o.jsxs("div", { className: "diagnostic-actions", children: [
      Ue(w.canRefreshDiagnostics, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("refreshDiagnostics", {}), children: "Refresh runtime" }),
      Ue(w.canOpenCachedAttention, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openCachedAttention", {}), children: "Cached attention explorer" }),
      Ue(w.canOpenLiveAttention, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openLiveAttention", {}), children: "Live attention capture" }),
      Ue(w.canUnloadModels, !1) && /* @__PURE__ */ o.jsx("button", { type: "button", className: "quiet", disabled: a, onClick: () => c("unloadModels", {}), children: "Unload models" })
    ] }),
    /* @__PURE__ */ o.jsx("section", { className: "metric-grid", children: x.length ? x.map((E) => /* @__PURE__ */ o.jsxs("article", { className: Jl(E.status), children: [
      /* @__PURE__ */ o.jsx("span", { children: E.label }),
      /* @__PURE__ */ o.jsx("strong", { children: E.value === null ? "Not captured in this mode" : String(E.value) }),
      E.detail && /* @__PURE__ */ o.jsx("small", { children: E.detail })
    ] }, E.label)) : /* @__PURE__ */ o.jsxs("article", { children: [
      /* @__PURE__ */ o.jsx("span", { children: "Runtime status" }),
      /* @__PURE__ */ o.jsx("strong", { children: (g == null ? void 0 : g.status) ?? "Ready" }),
      /* @__PURE__ */ o.jsx("small", { children: "Refresh to request a safe server summary." })
    ] }) }),
    (g == null ? void 0 : g.message) && /* @__PURE__ */ o.jsx("div", { className: "inline-notice info", children: g.message }),
    /* @__PURE__ */ o.jsx(lp, { diagnostics: g }),
    z && (g == null ? void 0 : g.details) && /* @__PURE__ */ o.jsxs("details", { className: "diagnostic-details", children: [
      /* @__PURE__ */ o.jsx("summary", { children: "Trusted-local details" }),
      /* @__PURE__ */ o.jsx("dl", { children: Object.entries(g.details).map(([E, k]) => /* @__PURE__ */ o.jsxs("div", { children: [
        /* @__PURE__ */ o.jsx("dt", { children: In(E) }),
        /* @__PURE__ */ o.jsx("dd", { children: typeof k == "object" ? JSON.stringify(k) : String(k) })
      ] }, E)) })
    ] }),
    /* @__PURE__ */ o.jsx(op, { recipes: u.recipes ?? [] })
  ] });
}
function up(u) {
  try {
    const a = URL.createObjectURL(new Blob([u.content], { type: u.mimeType ?? "application/json" })), c = document.createElement("a");
    return c.href = a, c.download = u.fileName, c.click(), URL.revokeObjectURL(a), !0;
  } catch {
    return !1;
  }
}
function ap({ componentKey: u, payload: a, setStateValue: c, setTriggerValue: g }) {
  var Je, ze, V, _, Le, Ce, ae, O;
  const w = a.viewState, x = ql.get(u) ?? { sequence: 0, draft: Vf(a.draft), workspace: (w == null ? void 0 : w.workspace) ?? "analyze", appearance: (w == null ? void 0 : w.appearance) ?? If, selectedRunId: null, seenDownload: null, focusWorkspace: null };
  ql.has(u) || ql.set(u, x);
  const [z, L] = ue.useState(x.workspace), [E, k] = ue.useState(x.appearance), [U, B] = ue.useState(x.draft), [J, ie] = ue.useState(x.selectedRunId), [ve, K] = ue.useState(!1), X = ue.useRef(null), b = (Je = a.actionReceipt) == null ? void 0 : Je.sequence;
  ue.useEffect(() => K(!1), [b, (ze = a.activity) == null ? void 0 : ze.status, a.runsRevision]), ue.useEffect(() => {
    w != null && w.workspace && w.workspace !== x.workspace && (x.workspace = w.workspace, L(w.workspace)), w != null && w.appearance && (w.appearance.theme !== x.appearance.theme || w.appearance.motion !== x.appearance.motion) && (x.appearance = w.appearance, k(w.appearance));
  }, [w == null ? void 0 : w.workspace, (V = w == null ? void 0 : w.appearance) == null ? void 0 : V.theme, (_ = w == null ? void 0 : w.appearance) == null ? void 0 : _.motion, x]), ue.useEffect(() => {
    document.documentElement.dataset.sirinMotion = E.motion;
  }, [E.motion]), ue.useEffect(() => {
    var h;
    const T = x.focusWorkspace;
    if (!T || (w == null ? void 0 : w.workspace) !== T) return;
    const P = (h = X.current) == null ? void 0 : h.querySelector(`[data-workspace-tab="${T}"]`);
    P && (P.focus(), x.focusWorkspace = null);
  }, [w == null ? void 0 : w.workspace, x]), ue.useEffect(() => {
    if (!a.download) {
      x.seenDownload = null;
      return;
    }
    const T = a.download ? `${a.download.fileName}:${a.download.content.length}` : null;
    if (a.download && T !== x.seenDownload && (x.seenDownload = T, up(a.download))) {
      x.sequence += 1;
      const P = { protocolVersion: a.protocolVersion, clientInstanceId: lc(), sequence: x.sequence, actionId: ic(), type: "clearDownload", expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: {} };
      g("action", P);
    }
  }, [a.download, a.protocolVersion, a.setupRevision, a.runsRevision, x, g]);
  const Ne = ve || ["queued", "running"].includes(((Le = a.activity) == null ? void 0 : Le.status) ?? ""), ge = (T) => {
    x.workspace = T, x.focusWorkspace = T, L(T), g("viewState", { workspace: T, appearance: x.appearance });
  }, fe = (T, P = !1) => {
    const h = { ...U, analyze: T };
    x.draft = h, B(h), P && c("draft", h);
  }, Te = (T, P = !1) => {
    const h = { ...U, quickPrompt: T };
    x.draft = h, B(h), P && c("draft", h);
  }, ke = (T) => {
    x.selectedRunId = T, ie(T), c("selectedRunId", T);
  }, pe = (T) => {
    var Z;
    const P = T.inputs ?? {}, S = { task: ((Z = T.setupSnapshot) == null ? void 0 : Z.task) ?? T.task ?? "faithfulness", mode: P.suppliedAnswer ? "supplied" : "generate", exampleId: null, context: P.context ?? "", question: P.question ?? "", answer: P.suppliedAnswer ?? "", prompt: P.prompt ?? "", sourceRunId: T.id };
    fe(S, !0), ge("analyze");
  }, Q = (T, P) => {
    if (Ne) return;
    x.sequence += 1;
    const h = { protocolVersion: a.protocolVersion, clientInstanceId: lc(), sequence: x.sequence, actionId: ic(), type: T, expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: P };
    K(!["selectRun"].includes(T)), g("action", h);
  }, Ze = (T, P) => {
    ge("compare"), Q("runCompare", { inputs: P, presetB: T });
  }, We = a.notices ?? [];
  return /* @__PURE__ */ o.jsx("div", { ref: X, className: "sirin-workspace", "data-theme": E.theme, "data-motion": E.motion, children: /* @__PURE__ */ o.jsxs("div", { className: "shell", children: [
    /* @__PURE__ */ o.jsx(Uf, { workspace: z, onWorkspace: ge, setup: a.setup, title: (Ce = a.ui) == null ? void 0 : Ce.title, subtitle: (ae = a.ui) == null ? void 0 : ae.subtitle }),
    We.length > 0 && /* @__PURE__ */ o.jsx("div", { className: "notice-stack", "aria-live": "polite", children: We.map((T, P) => /* @__PURE__ */ o.jsxs("div", { className: `inline-notice ${T.level ?? T.kind ?? "info"}`, children: [
      T.title && /* @__PURE__ */ o.jsx("b", { children: T.title }),
      /* @__PURE__ */ o.jsx("span", { children: T.message })
    ] }, P)) }),
    ((O = a.actionReceipt) == null ? void 0 : O.status) === "rejected" && /* @__PURE__ */ o.jsxs("div", { className: "inline-notice error receipt", role: "alert", children: [
      /* @__PURE__ */ o.jsx("b", { children: "Action rejected" }),
      /* @__PURE__ */ o.jsx("span", { children: a.actionReceipt.message ?? "The request could not be accepted." })
    ] }),
    z === "analyze" && /* @__PURE__ */ o.jsx(Gf, { payload: a, draft: U.analyze, setDraft: fe, busy: Ne, motion: E.motion, onAction: Q, onPrepareRerun: pe, onCompare: Ze }),
    z === "runs" && /* @__PURE__ */ o.jsx(tp, { payload: a, quickPrompt: U.quickPrompt, setQuickPrompt: Te, selectedId: J, setSelectedId: ke, busy: Ne, motion: E.motion, onAction: Q, onPrepareRerun: pe, onAnalyze: () => ge("analyze") }),
    z === "compare" && /* @__PURE__ */ o.jsx(_f, { payload: a, motion: E.motion, onAction: Q, onPrepareRerun: pe, onBack: () => ge("analyze") }),
    z === "diagnostics" && /* @__PURE__ */ o.jsx(sp, { payload: a, busy: Ne, onAction: Q }),
    /* @__PURE__ */ o.jsxs("footer", { children: [
      /* @__PURE__ */ o.jsxs("span", { children: [
        "SIRIN — ",
        /* @__PURE__ */ o.jsx("a", { href: "https://github.com/sb-ai-lab/SIRIN", target: "_blank", rel: "noreferrer", children: "github.com/sb-ai-lab/SIRIN" })
      ] }),
      /* @__PURE__ */ o.jsx("span", { children: "Detector confidence is not automatically a calibrated probability." })
    ] })
  ] }) });
}
const Cr = /* @__PURE__ */ new WeakMap(), zr = /* @__PURE__ */ new Map();
function cp(u) {
  for (const [a, c] of zr)
    a !== u && !c.isConnected && (ql.delete(a), zr.delete(a));
}
const dp = ({ data: u, key: a, parentElement: c, setStateValue: g, setTriggerValue: w }) => {
  Mf(), Ff(c);
  let x = Cr.get(c);
  if (x && (!x.container.isConnected || x.container.parentNode !== c)) {
    try {
      x.root.unmount();
    } catch {
    }
    x.container.remove(), Cr.delete(c), x = void 0;
  }
  if (!x) {
    c.querySelectorAll(".sirin-component-root").forEach((E) => E.remove());
    const L = document.createElement("div");
    L.className = "sirin-component-root", c.append(L), x = { container: L, root: xf.createRoot(L) }, Cr.set(c, x);
  }
  zr.set(a, x.container), cp(a);
  const z = x;
  return z.root.render(/* @__PURE__ */ o.jsx(ap, { componentKey: a, payload: u, setStateValue: g, setTriggerValue: w })), () => {
    Cr.get(c) === z && (Cr.delete(c), zr.get(a) === z.container && zr.delete(a), z.root.unmount(), z.container.remove());
  };
};
export {
  dp as default
};
