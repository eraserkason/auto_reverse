import{d as $,h,D as ao,E as so,F as co,G as Pe,H as ne,c as g,a as R,S as He,u as de,e as X,I as $e,J as ue,C as y,r as L,p as Q,K as p,b as k,L as Le,M as Y,O as U,P as ce,Q as oe,T as uo,U as J,k as Ce,V as fe,W as Fe,X as me,Y as vo,Z as ho,$ as Me,a0 as mo,a1 as po,a2 as go,s as O,v as se,m as N,a3 as we,n as je,R as B,A as ze,_ as ve,i as H,j as m,a4 as fo,a5 as te,a6 as Ae,y as q,z as re,l as V,o as bo,a7 as xo,w as j,a8 as yo,a9 as Co,B as wo,x as zo,aa as _o,ab as So}from"./index-CrjpUL23.js";import{N as ko,a as Io,b as Ro}from"./DrawerContent-B44P1vNV.js";import{C as To,N as No}from"./Dropdown-DNH4tivh.js";import{u as be}from"./use-merged-state-GBKmWucP.js";import{V as Po,u as Mo,c as pe}from"./Popover-C07QE1g7.js";import{f as ge}from"./get-BgFtjOeo.js";import"./next-frame-once-C5Ksf8W7.js";const Ao=$({name:"ChevronDownFilled",render(){return h("svg",{viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg"},h("path",{d:"M3.20041 5.73966C3.48226 5.43613 3.95681 5.41856 4.26034 5.70041L8 9.22652L11.7397 5.70041C12.0432 5.41856 12.5177 5.43613 12.7996 5.73966C13.0815 6.0432 13.0639 6.51775 12.7603 6.7996L8.51034 10.7996C8.22258 11.0668 7.77743 11.0668 7.48967 10.7996L3.23966 6.7996C2.93613 6.51775 2.91856 6.0432 3.20041 5.73966Z",fill:"currentColor"}))}});function Eo(e){const{baseColor:o,textColor2:t,bodyColor:a,cardColor:d,dividerColor:l,actionColor:v,scrollbarColor:u,scrollbarColorHover:i,invertedColor:c}=e;return{textColor:t,textColorInverted:"#FFF",color:a,colorEmbedded:v,headerColor:d,headerColorInverted:c,footerColor:v,footerColorInverted:c,headerBorderColor:l,headerBorderColorInverted:c,footerBorderColor:l,footerBorderColorInverted:c,siderBorderColor:l,siderBorderColorInverted:c,siderColor:d,siderColorInverted:c,siderToggleButtonBorder:`1px solid ${l}`,siderToggleButtonColor:o,siderToggleButtonIconColor:t,siderToggleButtonIconColorInverted:t,siderToggleBarColor:Pe(a,u),siderToggleBarColorHover:Pe(a,i),__invertScrollbar:"true"}}const _e=ao({name:"Layout",common:co,peers:{Scrollbar:so},self:Eo}),Ve=ne("n-layout-sider"),Se={type:String,default:"static"},Bo=g("layout",`
 color: var(--n-text-color);
 background-color: var(--n-color);
 box-sizing: border-box;
 position: relative;
 z-index: auto;
 flex: auto;
 overflow: hidden;
 transition:
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
`,[g("layout-scroll-container",`
 overflow-x: hidden;
 box-sizing: border-box;
 height: 100%;
 `),R("absolute-positioned",`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `)]),Oo={embedded:Boolean,position:Se,nativeScrollbar:{type:Boolean,default:!0},scrollbarProps:Object,onScroll:Function,contentClass:String,contentStyle:{type:[String,Object],default:""},hasSider:Boolean,siderPlacement:{type:String,default:"left"}},Ke=ne("n-layout");function Ue(e){return $({name:e?"LayoutContent":"Layout",props:Object.assign(Object.assign({},X.props),Oo),setup(o){const t=L(null),a=L(null),{mergedClsPrefixRef:d,inlineThemeDisabled:l}=de(o),v=X("Layout","-layout",Bo,_e,o,d);function u(s,I){if(o.nativeScrollbar){const{value:w}=t;w&&(I===void 0?w.scrollTo(s):w.scrollTo(s,I))}else{const{value:w}=a;w&&w.scrollTo(s,I)}}Q(Ke,o);let i=0,c=0;const A=s=>{var I;const w=s.target;i=w.scrollLeft,c=w.scrollTop,(I=o.onScroll)===null||I===void 0||I.call(o,s)};$e(()=>{if(o.nativeScrollbar){const s=t.value;s&&(s.scrollTop=c,s.scrollLeft=i)}});const P={display:"flex",flexWrap:"nowrap",width:"100%",flexDirection:"row"},b={scrollTo:u},C=y(()=>{const{common:{cubicBezierEaseInOut:s},self:I}=v.value;return{"--n-bezier":s,"--n-color":o.embedded?I.colorEmbedded:I.color,"--n-text-color":I.textColor}}),T=l?ue("layout",y(()=>o.embedded?"e":""),C,o):void 0;return Object.assign({mergedClsPrefix:d,scrollableElRef:t,scrollbarInstRef:a,hasSiderStyle:P,mergedTheme:v,handleNativeElScroll:A,cssVars:l?void 0:C,themeClass:T==null?void 0:T.themeClass,onRender:T==null?void 0:T.onRender},b)},render(){var o;const{mergedClsPrefix:t,hasSider:a}=this;(o=this.onRender)===null||o===void 0||o.call(this);const d=a?this.hasSiderStyle:void 0,l=[this.themeClass,e&&`${t}-layout-content`,`${t}-layout`,`${t}-layout--${this.position}-positioned`];return h("div",{class:l,style:this.cssVars},this.nativeScrollbar?h("div",{ref:"scrollableElRef",class:[`${t}-layout-scroll-container`,this.contentClass],style:[this.contentStyle,d],onScroll:this.handleNativeElScroll},this.$slots):h(He,Object.assign({},this.scrollbarProps,{onScroll:this.onScroll,ref:"scrollbarInstRef",theme:this.mergedTheme.peers.Scrollbar,themeOverrides:this.mergedTheme.peerOverrides.Scrollbar,contentClass:this.contentClass,contentStyle:[this.contentStyle,d]}),this.$slots))}})}const Ee=Ue(!1),Ho=Ue(!0),$o=g("layout-header",`
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 box-sizing: border-box;
 width: 100%;
 background-color: var(--n-color);
 color: var(--n-text-color);
`,[R("absolute-positioned",`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 `),R("bordered",`
 border-bottom: solid 1px var(--n-border-color);
 `)]),Lo={position:Se,inverted:Boolean,bordered:{type:Boolean,default:!1}},Fo=$({name:"LayoutHeader",props:Object.assign(Object.assign({},X.props),Lo),setup(e){const{mergedClsPrefixRef:o,inlineThemeDisabled:t}=de(e),a=X("Layout","-layout-header",$o,_e,e,o),d=y(()=>{const{common:{cubicBezierEaseInOut:v},self:u}=a.value,i={"--n-bezier":v};return e.inverted?(i["--n-color"]=u.headerColorInverted,i["--n-text-color"]=u.textColorInverted,i["--n-border-color"]=u.headerBorderColorInverted):(i["--n-color"]=u.headerColor,i["--n-text-color"]=u.textColor,i["--n-border-color"]=u.headerBorderColor),i}),l=t?ue("layout-header",y(()=>e.inverted?"a":"b"),d,e):void 0;return{mergedClsPrefix:o,cssVars:t?void 0:d,themeClass:l==null?void 0:l.themeClass,onRender:l==null?void 0:l.onRender}},render(){var e;const{mergedClsPrefix:o}=this;return(e=this.onRender)===null||e===void 0||e.call(this),h("div",{class:[`${o}-layout-header`,this.themeClass,this.position&&`${o}-layout-header--${this.position}-positioned`,this.bordered&&`${o}-layout-header--bordered`],style:this.cssVars},this.$slots)}}),jo=g("layout-sider",`
 flex-shrink: 0;
 box-sizing: border-box;
 position: relative;
 z-index: 1;
 color: var(--n-text-color);
 transition:
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier),
 min-width .3s var(--n-bezier),
 max-width .3s var(--n-bezier),
 transform .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 background-color: var(--n-color);
 display: flex;
 justify-content: flex-end;
`,[R("bordered",[p("border",`
 content: "";
 position: absolute;
 top: 0;
 bottom: 0;
 width: 1px;
 background-color: var(--n-border-color);
 transition: background-color .3s var(--n-bezier);
 `)]),p("left-placement",[R("bordered",[p("border",`
 right: 0;
 `)])]),R("right-placement",`
 justify-content: flex-start;
 `,[R("bordered",[p("border",`
 left: 0;
 `)]),R("collapsed",[g("layout-toggle-button",[g("base-icon",`
 transform: rotate(180deg);
 `)]),g("layout-toggle-bar",[k("&:hover",[p("top",{transform:"rotate(-12deg) scale(1.15) translateY(-2px)"}),p("bottom",{transform:"rotate(12deg) scale(1.15) translateY(2px)"})])])]),g("layout-toggle-button",`
 left: 0;
 transform: translateX(-50%) translateY(-50%);
 `,[g("base-icon",`
 transform: rotate(0);
 `)]),g("layout-toggle-bar",`
 left: -28px;
 transform: rotate(180deg);
 `,[k("&:hover",[p("top",{transform:"rotate(12deg) scale(1.15) translateY(-2px)"}),p("bottom",{transform:"rotate(-12deg) scale(1.15) translateY(2px)"})])])]),R("collapsed",[g("layout-toggle-bar",[k("&:hover",[p("top",{transform:"rotate(-12deg) scale(1.15) translateY(-2px)"}),p("bottom",{transform:"rotate(12deg) scale(1.15) translateY(2px)"})])]),g("layout-toggle-button",[g("base-icon",`
 transform: rotate(0);
 `)])]),g("layout-toggle-button",`
 transition:
 color .3s var(--n-bezier),
 right .3s var(--n-bezier),
 left .3s var(--n-bezier),
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 cursor: pointer;
 width: 24px;
 height: 24px;
 position: absolute;
 top: 50%;
 right: 0;
 border-radius: 50%;
 display: flex;
 align-items: center;
 justify-content: center;
 font-size: 18px;
 color: var(--n-toggle-button-icon-color);
 border: var(--n-toggle-button-border);
 background-color: var(--n-toggle-button-color);
 box-shadow: 0 2px 4px 0px rgba(0, 0, 0, .06);
 transform: translateX(50%) translateY(-50%);
 z-index: 1;
 `,[g("base-icon",`
 transition: transform .3s var(--n-bezier);
 transform: rotate(180deg);
 `)]),g("layout-toggle-bar",`
 cursor: pointer;
 height: 72px;
 width: 32px;
 position: absolute;
 top: calc(50% - 36px);
 right: -28px;
 `,[p("top, bottom",`
 position: absolute;
 width: 4px;
 border-radius: 2px;
 height: 38px;
 left: 14px;
 transition: 
 background-color .3s var(--n-bezier),
 transform .3s var(--n-bezier);
 `),p("bottom",`
 position: absolute;
 top: 34px;
 `),k("&:hover",[p("top",{transform:"rotate(12deg) scale(1.15) translateY(-2px)"}),p("bottom",{transform:"rotate(-12deg) scale(1.15) translateY(2px)"})]),p("top, bottom",{backgroundColor:"var(--n-toggle-bar-color)"}),k("&:hover",[p("top, bottom",{backgroundColor:"var(--n-toggle-bar-color-hover)"})])]),p("border",`
 position: absolute;
 top: 0;
 right: 0;
 bottom: 0;
 width: 1px;
 transition: background-color .3s var(--n-bezier);
 `),g("layout-sider-scroll-container",`
 flex-grow: 1;
 flex-shrink: 0;
 box-sizing: border-box;
 height: 100%;
 opacity: 0;
 transition: opacity .3s var(--n-bezier);
 max-width: 100%;
 `),R("show-content",[g("layout-sider-scroll-container",{opacity:1})]),R("absolute-positioned",`
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 `)]),Vo=$({props:{clsPrefix:{type:String,required:!0},onClick:Function},render(){const{clsPrefix:e}=this;return h("div",{onClick:this.onClick,class:`${e}-layout-toggle-bar`},h("div",{class:`${e}-layout-toggle-bar__top`}),h("div",{class:`${e}-layout-toggle-bar__bottom`}))}}),Ko=$({name:"LayoutToggleButton",props:{clsPrefix:{type:String,required:!0},onClick:Function},render(){const{clsPrefix:e}=this;return h("div",{class:`${e}-layout-toggle-button`,onClick:this.onClick},h(Le,{clsPrefix:e},{default:()=>h(To,null)}))}}),Uo={position:Se,bordered:Boolean,collapsedWidth:{type:Number,default:48},width:{type:[Number,String],default:272},contentClass:String,contentStyle:{type:[String,Object],default:""},collapseMode:{type:String,default:"transform"},collapsed:{type:Boolean,default:void 0},defaultCollapsed:Boolean,showCollapsedContent:{type:Boolean,default:!0},showTrigger:{type:[Boolean,String],default:!1},nativeScrollbar:{type:Boolean,default:!0},inverted:Boolean,scrollbarProps:Object,triggerClass:String,triggerStyle:[String,Object],collapsedTriggerClass:String,collapsedTriggerStyle:[String,Object],"onUpdate:collapsed":[Function,Array],onUpdateCollapsed:[Function,Array],onAfterEnter:Function,onAfterLeave:Function,onExpand:[Function,Array],onCollapse:[Function,Array],onScroll:Function},Do=$({name:"LayoutSider",props:Object.assign(Object.assign({},X.props),Uo),setup(e){const o=Y(Ke),t=L(null),a=L(null),d=L(e.defaultCollapsed),l=be(ce(e,"collapsed"),d),v=y(()=>ge(l.value?e.collapsedWidth:e.width)),u=y(()=>e.collapseMode!=="transform"?{}:{minWidth:ge(e.width)}),i=y(()=>o?o.siderPlacement:"left");function c(E,_){if(e.nativeScrollbar){const{value:S}=t;S&&(_===void 0?S.scrollTo(E):S.scrollTo(E,_))}else{const{value:S}=a;S&&S.scrollTo(E,_)}}function A(){const{"onUpdate:collapsed":E,onUpdateCollapsed:_,onExpand:S,onCollapse:W}=e,{value:D}=l;_&&U(_,!D),E&&U(E,!D),d.value=!D,D?S&&U(S):W&&U(W)}let P=0,b=0;const C=E=>{var _;const S=E.target;P=S.scrollLeft,b=S.scrollTop,(_=e.onScroll)===null||_===void 0||_.call(e,E)};$e(()=>{if(e.nativeScrollbar){const E=t.value;E&&(E.scrollTop=b,E.scrollLeft=P)}}),Q(Ve,{collapsedRef:l,collapseModeRef:ce(e,"collapseMode")});const{mergedClsPrefixRef:T,inlineThemeDisabled:s}=de(e),I=X("Layout","-layout-sider",jo,_e,e,T);function w(E){var _,S;E.propertyName==="max-width"&&(l.value?(_=e.onAfterLeave)===null||_===void 0||_.call(e):(S=e.onAfterEnter)===null||S===void 0||S.call(e))}const ee={scrollTo:c},G=y(()=>{const{common:{cubicBezierEaseInOut:E},self:_}=I.value,{siderToggleButtonColor:S,siderToggleButtonBorder:W,siderToggleBarColor:D,siderToggleBarColorHover:he}=_,F={"--n-bezier":E,"--n-toggle-button-color":S,"--n-toggle-button-border":W,"--n-toggle-bar-color":D,"--n-toggle-bar-color-hover":he};return e.inverted?(F["--n-color"]=_.siderColorInverted,F["--n-text-color"]=_.textColorInverted,F["--n-border-color"]=_.siderBorderColorInverted,F["--n-toggle-button-icon-color"]=_.siderToggleButtonIconColorInverted,F.__invertScrollbar=_.__invertScrollbar):(F["--n-color"]=_.siderColor,F["--n-text-color"]=_.textColor,F["--n-border-color"]=_.siderBorderColor,F["--n-toggle-button-icon-color"]=_.siderToggleButtonIconColor),F}),K=s?ue("layout-sider",y(()=>e.inverted?"a":"b"),G,e):void 0;return Object.assign({scrollableElRef:t,scrollbarInstRef:a,mergedClsPrefix:T,mergedTheme:I,styleMaxWidth:v,mergedCollapsed:l,scrollContainerStyle:u,siderPlacement:i,handleNativeElScroll:C,handleTransitionend:w,handleTriggerClick:A,inlineThemeDisabled:s,cssVars:G,themeClass:K==null?void 0:K.themeClass,onRender:K==null?void 0:K.onRender},ee)},render(){var e;const{mergedClsPrefix:o,mergedCollapsed:t,showTrigger:a}=this;return(e=this.onRender)===null||e===void 0||e.call(this),h("aside",{class:[`${o}-layout-sider`,this.themeClass,`${o}-layout-sider--${this.position}-positioned`,`${o}-layout-sider--${this.siderPlacement}-placement`,this.bordered&&`${o}-layout-sider--bordered`,t&&`${o}-layout-sider--collapsed`,(!t||this.showCollapsedContent)&&`${o}-layout-sider--show-content`],onTransitionend:this.handleTransitionend,style:[this.inlineThemeDisabled?void 0:this.cssVars,{maxWidth:this.styleMaxWidth,width:ge(this.width)}]},this.nativeScrollbar?h("div",{class:[`${o}-layout-sider-scroll-container`,this.contentClass],onScroll:this.handleNativeElScroll,style:[this.scrollContainerStyle,{overflow:"auto"},this.contentStyle],ref:"scrollableElRef"},this.$slots):h(He,Object.assign({},this.scrollbarProps,{onScroll:this.onScroll,ref:"scrollbarInstRef",style:this.scrollContainerStyle,contentStyle:this.contentStyle,contentClass:this.contentClass,theme:this.mergedTheme.peers.Scrollbar,themeOverrides:this.mergedTheme.peerOverrides.Scrollbar,builtinThemeOverrides:this.inverted&&this.cssVars.__invertScrollbar==="true"?{colorHover:"rgba(255, 255, 255, .4)",color:"rgba(255, 255, 255, .3)"}:void 0}),this.$slots),a?a==="bar"?h(Vo,{clsPrefix:o,class:t?this.collapsedTriggerClass:this.triggerClass,style:t?this.collapsedTriggerStyle:this.triggerStyle,onClick:this.handleTriggerClick}):h(Ko,{clsPrefix:o,class:t?this.collapsedTriggerClass:this.triggerClass,style:t?this.collapsedTriggerStyle:this.triggerStyle,onClick:this.handleTriggerClick}):null,this.bordered?h("div",{class:`${o}-layout-sider__border`}):null)}}),le=ne("n-menu"),De=ne("n-submenu"),ke=ne("n-menu-item-group"),Be=[k("&::before","background-color: var(--n-item-color-hover);"),p("arrow",`
 color: var(--n-arrow-color-hover);
 `),p("icon",`
 color: var(--n-item-icon-color-hover);
 `),g("menu-item-content-header",`
 color: var(--n-item-text-color-hover);
 `,[k("a",`
 color: var(--n-item-text-color-hover);
 `),p("extra",`
 color: var(--n-item-text-color-hover);
 `)])],Oe=[p("icon",`
 color: var(--n-item-icon-color-hover-horizontal);
 `),g("menu-item-content-header",`
 color: var(--n-item-text-color-hover-horizontal);
 `,[k("a",`
 color: var(--n-item-text-color-hover-horizontal);
 `),p("extra",`
 color: var(--n-item-text-color-hover-horizontal);
 `)])],Go=k([g("menu",`
 background-color: var(--n-color);
 color: var(--n-item-text-color);
 overflow: hidden;
 transition: background-color .3s var(--n-bezier);
 box-sizing: border-box;
 font-size: var(--n-font-size);
 padding-bottom: 6px;
 `,[R("horizontal",`
 max-width: 100%;
 width: 100%;
 display: flex;
 overflow: hidden;
 padding-bottom: 0;
 `,[g("submenu","margin: 0;"),g("menu-item","margin: 0;"),g("menu-item-content",`
 padding: 0 20px;
 border-bottom: 2px solid #0000;
 `,[k("&::before","display: none;"),R("selected","border-bottom: 2px solid var(--n-border-color-horizontal)")]),g("menu-item-content",[R("selected",[p("icon","color: var(--n-item-icon-color-active-horizontal);"),g("menu-item-content-header",`
 color: var(--n-item-text-color-active-horizontal);
 `,[k("a","color: var(--n-item-text-color-active-horizontal);"),p("extra","color: var(--n-item-text-color-active-horizontal);")])]),R("child-active",`
 border-bottom: 2px solid var(--n-border-color-horizontal);
 `,[g("menu-item-content-header",`
 color: var(--n-item-text-color-child-active-horizontal);
 `,[k("a",`
 color: var(--n-item-text-color-child-active-horizontal);
 `),p("extra",`
 color: var(--n-item-text-color-child-active-horizontal);
 `)]),p("icon",`
 color: var(--n-item-icon-color-child-active-horizontal);
 `)]),oe("disabled",[oe("selected, child-active",[k("&:focus-within",Oe)]),R("selected",[Z(null,[p("icon","color: var(--n-item-icon-color-active-hover-horizontal);"),g("menu-item-content-header",`
 color: var(--n-item-text-color-active-hover-horizontal);
 `,[k("a","color: var(--n-item-text-color-active-hover-horizontal);"),p("extra","color: var(--n-item-text-color-active-hover-horizontal);")])])]),R("child-active",[Z(null,[p("icon","color: var(--n-item-icon-color-child-active-hover-horizontal);"),g("menu-item-content-header",`
 color: var(--n-item-text-color-child-active-hover-horizontal);
 `,[k("a","color: var(--n-item-text-color-child-active-hover-horizontal);"),p("extra","color: var(--n-item-text-color-child-active-hover-horizontal);")])])]),Z("border-bottom: 2px solid var(--n-border-color-horizontal);",Oe)]),g("menu-item-content-header",[k("a","color: var(--n-item-text-color-horizontal);")])])]),oe("responsive",[g("menu-item-content-header",`
 overflow: hidden;
 text-overflow: ellipsis;
 `)]),R("collapsed",[g("menu-item-content",[R("selected",[k("&::before",`
 background-color: var(--n-item-color-active-collapsed) !important;
 `)]),g("menu-item-content-header","opacity: 0;"),p("arrow","opacity: 0;"),p("icon","color: var(--n-item-icon-color-collapsed);")])]),g("menu-item",`
 height: var(--n-item-height);
 margin-top: 6px;
 position: relative;
 `),g("menu-item-content",`
 box-sizing: border-box;
 line-height: 1.75;
 height: 100%;
 display: grid;
 grid-template-areas: "icon content arrow";
 grid-template-columns: auto 1fr auto;
 align-items: center;
 cursor: pointer;
 position: relative;
 padding-right: 18px;
 transition:
 background-color .3s var(--n-bezier),
 padding-left .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[k("> *","z-index: 1;"),k("&::before",`
 z-index: auto;
 content: "";
 background-color: #0000;
 position: absolute;
 left: 8px;
 right: 8px;
 top: 0;
 bottom: 0;
 pointer-events: none;
 border-radius: var(--n-border-radius);
 transition: background-color .3s var(--n-bezier);
 `),R("disabled",`
 opacity: .45;
 cursor: not-allowed;
 `),R("collapsed",[p("arrow","transform: rotate(0);")]),R("selected",[k("&::before","background-color: var(--n-item-color-active);"),p("arrow","color: var(--n-arrow-color-active);"),p("icon","color: var(--n-item-icon-color-active);"),g("menu-item-content-header",`
 color: var(--n-item-text-color-active);
 `,[k("a","color: var(--n-item-text-color-active);"),p("extra","color: var(--n-item-text-color-active);")])]),R("child-active",[g("menu-item-content-header",`
 color: var(--n-item-text-color-child-active);
 `,[k("a",`
 color: var(--n-item-text-color-child-active);
 `),p("extra",`
 color: var(--n-item-text-color-child-active);
 `)]),p("arrow",`
 color: var(--n-arrow-color-child-active);
 `),p("icon",`
 color: var(--n-item-icon-color-child-active);
 `)]),oe("disabled",[oe("selected, child-active",[k("&:focus-within",Be)]),R("selected",[Z(null,[p("arrow","color: var(--n-arrow-color-active-hover);"),p("icon","color: var(--n-item-icon-color-active-hover);"),g("menu-item-content-header",`
 color: var(--n-item-text-color-active-hover);
 `,[k("a","color: var(--n-item-text-color-active-hover);"),p("extra","color: var(--n-item-text-color-active-hover);")])])]),R("child-active",[Z(null,[p("arrow","color: var(--n-arrow-color-child-active-hover);"),p("icon","color: var(--n-item-icon-color-child-active-hover);"),g("menu-item-content-header",`
 color: var(--n-item-text-color-child-active-hover);
 `,[k("a","color: var(--n-item-text-color-child-active-hover);"),p("extra","color: var(--n-item-text-color-child-active-hover);")])])]),R("selected",[Z(null,[k("&::before","background-color: var(--n-item-color-active-hover);")])]),Z(null,Be)]),p("icon",`
 grid-area: icon;
 color: var(--n-item-icon-color);
 transition:
 color .3s var(--n-bezier),
 font-size .3s var(--n-bezier),
 margin-right .3s var(--n-bezier);
 box-sizing: content-box;
 display: inline-flex;
 align-items: center;
 justify-content: center;
 `),p("arrow",`
 grid-area: arrow;
 font-size: 16px;
 color: var(--n-arrow-color);
 transform: rotate(180deg);
 opacity: 1;
 transition:
 color .3s var(--n-bezier),
 transform 0.2s var(--n-bezier),
 opacity 0.2s var(--n-bezier);
 `),g("menu-item-content-header",`
 grid-area: content;
 transition:
 color .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 opacity: 1;
 white-space: nowrap;
 color: var(--n-item-text-color);
 `,[k("a",`
 outline: none;
 text-decoration: none;
 transition: color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 `,[k("&::before",`
 content: "";
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `)]),p("extra",`
 font-size: .93em;
 color: var(--n-group-text-color);
 transition: color .3s var(--n-bezier);
 `)])]),g("submenu",`
 cursor: pointer;
 position: relative;
 margin-top: 6px;
 `,[g("menu-item-content",`
 height: var(--n-item-height);
 `),g("submenu-children",`
 overflow: hidden;
 padding: 0;
 `,[uo({duration:".2s"})])]),g("menu-item-group",[g("menu-item-group-title",`
 margin-top: 6px;
 color: var(--n-group-text-color);
 cursor: default;
 font-size: .93em;
 height: 36px;
 display: flex;
 align-items: center;
 transition:
 padding-left .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `)])]),g("menu-tooltip",[k("a",`
 color: inherit;
 text-decoration: none;
 `)]),g("menu-divider",`
 transition: background-color .3s var(--n-bezier);
 background-color: var(--n-divider-color);
 height: 1px;
 margin: 6px 18px;
 `)]);function Z(e,o){return[R("hover",e,o),k("&:hover",e,o)]}const Ge=$({name:"MenuOptionContent",props:{collapsed:Boolean,disabled:Boolean,title:[String,Function],icon:Function,extra:[String,Function],showArrow:Boolean,childActive:Boolean,hover:Boolean,paddingLeft:Number,selected:Boolean,maxIconSize:{type:Number,required:!0},activeIconSize:{type:Number,required:!0},iconMarginRight:{type:Number,required:!0},clsPrefix:{type:String,required:!0},onClick:Function,tmNode:{type:Object,required:!0},isEllipsisPlaceholder:Boolean},setup(e){const{props:o}=Y(le);return{menuProps:o,style:y(()=>{const{paddingLeft:t}=e;return{paddingLeft:t&&`${t}px`}}),iconStyle:y(()=>{const{maxIconSize:t,activeIconSize:a,iconMarginRight:d}=e;return{width:`${t}px`,height:`${t}px`,fontSize:`${a}px`,marginRight:`${d}px`}})}},render(){const{clsPrefix:e,tmNode:o,menuProps:{renderIcon:t,renderLabel:a,renderExtra:d,expandIcon:l}}=this,v=t?t(o.rawNode):J(this.icon);return h("div",{onClick:u=>{var i;(i=this.onClick)===null||i===void 0||i.call(this,u)},role:"none",class:[`${e}-menu-item-content`,{[`${e}-menu-item-content--selected`]:this.selected,[`${e}-menu-item-content--collapsed`]:this.collapsed,[`${e}-menu-item-content--child-active`]:this.childActive,[`${e}-menu-item-content--disabled`]:this.disabled,[`${e}-menu-item-content--hover`]:this.hover}],style:this.style},v&&h("div",{class:`${e}-menu-item-content__icon`,style:this.iconStyle,role:"none"},[v]),h("div",{class:`${e}-menu-item-content-header`,role:"none"},this.isEllipsisPlaceholder?this.title:a?a(o.rawNode):J(this.title),this.extra||d?h("span",{class:`${e}-menu-item-content-header__extra`}," ",d?d(o.rawNode):J(this.extra)):null),this.showArrow?h(Le,{ariaHidden:!0,class:`${e}-menu-item-content__arrow`,clsPrefix:e},{default:()=>l?l(o.rawNode):h(Ao,null)}):null)}}),ae=8;function Ie(e){const o=Y(le),{props:t,mergedCollapsedRef:a}=o,d=Y(De,null),l=Y(ke,null),v=y(()=>t.mode==="horizontal"),u=y(()=>v.value?t.dropdownPlacement:"tmNodes"in e?"right-start":"right"),i=y(()=>{var b;return Math.max((b=t.collapsedIconSize)!==null&&b!==void 0?b:t.iconSize,t.iconSize)}),c=y(()=>{var b;return!v.value&&e.root&&a.value&&(b=t.collapsedIconSize)!==null&&b!==void 0?b:t.iconSize}),A=y(()=>{if(v.value)return;const{collapsedWidth:b,indent:C,rootIndent:T}=t,{root:s,isGroup:I}=e,w=T===void 0?C:T;return s?a.value?b/2-i.value/2:w:l&&typeof l.paddingLeftRef.value=="number"?C/2+l.paddingLeftRef.value:d&&typeof d.paddingLeftRef.value=="number"?(I?C/2:C)+d.paddingLeftRef.value:0}),P=y(()=>{const{collapsedWidth:b,indent:C,rootIndent:T}=t,{value:s}=i,{root:I}=e;return v.value||!I||!a.value?ae:(T===void 0?C:T)+s+ae-(b+s)/2});return{dropdownPlacement:u,activeIconSize:c,maxIconSize:i,paddingLeft:A,iconMarginRight:P,NMenu:o,NSubmenu:d,NMenuOptionGroup:l}}const Re={internalKey:{type:[String,Number],required:!0},root:Boolean,isGroup:Boolean,level:{type:Number,required:!0},title:[String,Function],extra:[String,Function]},Wo=$({name:"MenuDivider",setup(){const e=Y(le),{mergedClsPrefixRef:o,isHorizontalRef:t}=e;return()=>t.value?null:h("div",{class:`${o.value}-menu-divider`})}}),We=Object.assign(Object.assign({},Re),{tmNode:{type:Object,required:!0},disabled:Boolean,icon:Function,onClick:Function}),qo=Ce(We),Yo=$({name:"MenuOption",props:We,setup(e){const o=Ie(e),{NSubmenu:t,NMenu:a,NMenuOptionGroup:d}=o,{props:l,mergedClsPrefixRef:v,mergedCollapsedRef:u}=a,i=t?t.mergedDisabledRef:d?d.mergedDisabledRef:{value:!1},c=y(()=>i.value||e.disabled);function A(b){const{onClick:C}=e;C&&C(b)}function P(b){c.value||(a.doSelect(e.internalKey,e.tmNode.rawNode),A(b))}return{mergedClsPrefix:v,dropdownPlacement:o.dropdownPlacement,paddingLeft:o.paddingLeft,iconMarginRight:o.iconMarginRight,maxIconSize:o.maxIconSize,activeIconSize:o.activeIconSize,mergedTheme:a.mergedThemeRef,menuProps:l,dropdownEnabled:fe(()=>e.root&&u.value&&l.mode!=="horizontal"&&!c.value),selected:fe(()=>a.mergedValueRef.value===e.internalKey),mergedDisabled:c,handleClick:P}},render(){const{mergedClsPrefix:e,mergedTheme:o,tmNode:t,menuProps:{renderLabel:a,nodeProps:d}}=this,l=d==null?void 0:d(t.rawNode);return h("div",Object.assign({},l,{role:"menuitem",class:[`${e}-menu-item`,l==null?void 0:l.class]}),h(ko,{theme:o.peers.Tooltip,themeOverrides:o.peerOverrides.Tooltip,trigger:"hover",placement:this.dropdownPlacement,disabled:!this.dropdownEnabled||this.title===void 0,internalExtraClass:["menu-tooltip"]},{default:()=>a?a(t.rawNode):J(this.title),trigger:()=>h(Ge,{tmNode:t,clsPrefix:e,paddingLeft:this.paddingLeft,iconMarginRight:this.iconMarginRight,maxIconSize:this.maxIconSize,activeIconSize:this.activeIconSize,selected:this.selected,title:this.title,extra:this.extra,disabled:this.mergedDisabled,icon:this.icon,onClick:this.handleClick})}))}}),qe=Object.assign(Object.assign({},Re),{tmNode:{type:Object,required:!0},tmNodes:{type:Array,required:!0}}),Xo=Ce(qe),Zo=$({name:"MenuOptionGroup",props:qe,setup(e){const o=Ie(e),{NSubmenu:t}=o,a=y(()=>t!=null&&t.mergedDisabledRef.value?!0:e.tmNode.disabled);Q(ke,{paddingLeftRef:o.paddingLeft,mergedDisabledRef:a});const{mergedClsPrefixRef:d,props:l}=Y(le);return function(){const{value:v}=d,u=o.paddingLeft.value,{nodeProps:i}=l,c=i==null?void 0:i(e.tmNode.rawNode);return h("div",{class:`${v}-menu-item-group`,role:"group"},h("div",Object.assign({},c,{class:[`${v}-menu-item-group-title`,c==null?void 0:c.class],style:[(c==null?void 0:c.style)||"",u!==void 0?`padding-left: ${u}px;`:""]}),J(e.title),e.extra?h(Fe,null," ",J(e.extra)):null),h("div",null,e.tmNodes.map(A=>Te(A,l))))}}});function xe(e){return e.type==="divider"||e.type==="render"}function Jo(e){return e.type==="divider"}function Te(e,o){const{rawNode:t}=e,{show:a}=t;if(a===!1)return null;if(xe(t))return Jo(t)?h(Wo,Object.assign({key:e.key},t.props)):null;const{labelField:d}=o,{key:l,level:v,isGroup:u}=e,i=Object.assign(Object.assign({},t),{title:t.title||t[d],extra:t.titleExtra||t.extra,key:l,internalKey:l,level:v,root:v===0,isGroup:u});return e.children?e.isGroup?h(Zo,me(i,Xo,{tmNode:e,tmNodes:e.children,key:l})):h(ye,me(i,Qo,{key:l,rawNodes:t[o.childrenField],tmNodes:e.children,tmNode:e})):h(Yo,me(i,qo,{key:l,tmNode:e}))}const Ye=Object.assign(Object.assign({},Re),{rawNodes:{type:Array,default:()=>[]},tmNodes:{type:Array,default:()=>[]},tmNode:{type:Object,required:!0},disabled:Boolean,icon:Function,onClick:Function,domId:String,virtualChildActive:{type:Boolean,default:void 0},isEllipsisPlaceholder:Boolean}),Qo=Ce(Ye),ye=$({name:"Submenu",props:Ye,setup(e){const o=Ie(e),{NMenu:t,NSubmenu:a}=o,{props:d,mergedCollapsedRef:l,mergedThemeRef:v}=t,u=y(()=>{const{disabled:b}=e;return a!=null&&a.mergedDisabledRef.value||d.disabled?!0:b}),i=L(!1);Q(De,{paddingLeftRef:o.paddingLeft,mergedDisabledRef:u}),Q(ke,null);function c(){const{onClick:b}=e;b&&b()}function A(){u.value||(l.value||t.toggleExpand(e.internalKey),c())}function P(b){i.value=b}return{menuProps:d,mergedTheme:v,doSelect:t.doSelect,inverted:t.invertedRef,isHorizontal:t.isHorizontalRef,mergedClsPrefix:t.mergedClsPrefixRef,maxIconSize:o.maxIconSize,activeIconSize:o.activeIconSize,iconMarginRight:o.iconMarginRight,dropdownPlacement:o.dropdownPlacement,dropdownShow:i,paddingLeft:o.paddingLeft,mergedDisabled:u,mergedValue:t.mergedValueRef,childActive:fe(()=>{var b;return(b=e.virtualChildActive)!==null&&b!==void 0?b:t.activePathRef.value.includes(e.internalKey)}),collapsed:y(()=>d.mode==="horizontal"?!1:l.value?!0:!t.mergedExpandedKeysRef.value.includes(e.internalKey)),dropdownEnabled:y(()=>!u.value&&(d.mode==="horizontal"||l.value)),handlePopoverShowChange:P,handleClick:A}},render(){var e;const{mergedClsPrefix:o,menuProps:{renderIcon:t,renderLabel:a}}=this,d=()=>{const{isHorizontal:v,paddingLeft:u,collapsed:i,mergedDisabled:c,maxIconSize:A,activeIconSize:P,title:b,childActive:C,icon:T,handleClick:s,menuProps:{nodeProps:I},dropdownShow:w,iconMarginRight:ee,tmNode:G,mergedClsPrefix:K,isEllipsisPlaceholder:E,extra:_}=this,S=I==null?void 0:I(G.rawNode);return h("div",Object.assign({},S,{class:[`${K}-menu-item`,S==null?void 0:S.class],role:"menuitem"}),h(Ge,{tmNode:G,paddingLeft:u,collapsed:i,disabled:c,iconMarginRight:ee,maxIconSize:A,activeIconSize:P,title:b,extra:_,showArrow:!v,childActive:C,clsPrefix:K,icon:T,hover:w,onClick:s,isEllipsisPlaceholder:E}))},l=()=>h(vo,null,{default:()=>{const{tmNodes:v,collapsed:u}=this;return u?null:h("div",{class:`${o}-submenu-children`,role:"menu"},v.map(i=>Te(i,this.menuProps)))}});return this.root?h(No,Object.assign({size:"large",trigger:"hover"},(e=this.menuProps)===null||e===void 0?void 0:e.dropdownProps,{themeOverrides:this.mergedTheme.peerOverrides.Dropdown,theme:this.mergedTheme.peers.Dropdown,builtinThemeOverrides:{fontSizeLarge:"14px",optionIconSizeLarge:"18px"},value:this.mergedValue,disabled:!this.dropdownEnabled,placement:this.dropdownPlacement,keyField:this.menuProps.keyField,labelField:this.menuProps.labelField,childrenField:this.menuProps.childrenField,onUpdateShow:this.handlePopoverShowChange,options:this.rawNodes,onSelect:this.doSelect,inverted:this.inverted,renderIcon:t,renderLabel:a}),{default:()=>h("div",{class:`${o}-submenu`,role:"menu","aria-expanded":!this.collapsed,id:this.domId},d(),this.isHorizontal?null:l())}):h("div",{class:`${o}-submenu`,role:"menu","aria-expanded":!this.collapsed,id:this.domId},d(),l())}}),et=Object.assign(Object.assign({},X.props),{options:{type:Array,default:()=>[]},collapsed:{type:Boolean,default:void 0},collapsedWidth:{type:Number,default:48},iconSize:{type:Number,default:20},collapsedIconSize:{type:Number,default:24},rootIndent:Number,indent:{type:Number,default:32},labelField:{type:String,default:"label"},keyField:{type:String,default:"key"},childrenField:{type:String,default:"children"},disabledField:{type:String,default:"disabled"},defaultExpandAll:Boolean,defaultExpandedKeys:Array,expandedKeys:Array,value:[String,Number],defaultValue:{type:[String,Number],default:null},mode:{type:String,default:"vertical"},watchProps:{type:Array,default:void 0},disabled:Boolean,show:{type:Boolean,default:!0},inverted:Boolean,"onUpdate:expandedKeys":[Function,Array],onUpdateExpandedKeys:[Function,Array],onUpdateValue:[Function,Array],"onUpdate:value":[Function,Array],expandIcon:Function,renderIcon:Function,renderLabel:Function,renderExtra:Function,dropdownProps:Object,accordion:Boolean,nodeProps:Function,dropdownPlacement:{type:String,default:"bottom"},responsive:Boolean,items:Array,onOpenNamesChange:[Function,Array],onSelect:[Function,Array],onExpandedNamesChange:[Function,Array],expandedNames:Array,defaultExpandedNames:Array}),ot=$({name:"Menu",inheritAttrs:!1,props:et,setup(e){const{mergedClsPrefixRef:o,inlineThemeDisabled:t}=de(e),a=X("Menu","-menu",Go,go,e,o),d=Y(Ve,null),l=y(()=>{var f;const{collapsed:z}=e;if(z!==void 0)return z;if(d){const{collapseModeRef:r,collapsedRef:x}=d;if(r.value==="width")return(f=x.value)!==null&&f!==void 0?f:!1}return!1}),v=y(()=>{const{keyField:f,childrenField:z,disabledField:r}=e;return pe(e.items||e.options,{getIgnored(x){return xe(x)},getChildren(x){return x[z]},getDisabled(x){return x[r]},getKey(x){var M;return(M=x[f])!==null&&M!==void 0?M:x.name}})}),u=y(()=>new Set(v.value.treeNodes.map(f=>f.key))),{watchProps:i}=e,c=L(null);i!=null&&i.includes("defaultValue")?Me(()=>{c.value=e.defaultValue}):c.value=e.defaultValue;const A=ce(e,"value"),P=be(A,c),b=L([]),C=()=>{b.value=e.defaultExpandAll?v.value.getNonLeafKeys():e.defaultExpandedNames||e.defaultExpandedKeys||v.value.getPath(P.value,{includeSelf:!1}).keyPath};i!=null&&i.includes("defaultExpandedKeys")?Me(C):C();const T=Mo(e,["expandedNames","expandedKeys"]),s=be(T,b),I=y(()=>v.value.treeNodes),w=y(()=>v.value.getPath(P.value).keyPath);Q(le,{props:e,mergedCollapsedRef:l,mergedThemeRef:a,mergedValueRef:P,mergedExpandedKeysRef:s,activePathRef:w,mergedClsPrefixRef:o,isHorizontalRef:y(()=>e.mode==="horizontal"),invertedRef:ce(e,"inverted"),doSelect:ee,toggleExpand:K});function ee(f,z){const{"onUpdate:value":r,onUpdateValue:x,onSelect:M}=e;x&&U(x,f,z),r&&U(r,f,z),M&&U(M,f,z),c.value=f}function G(f){const{"onUpdate:expandedKeys":z,onUpdateExpandedKeys:r,onExpandedNamesChange:x,onOpenNamesChange:M}=e;z&&U(z,f),r&&U(r,f),x&&U(x,f),M&&U(M,f),b.value=f}function K(f){const z=Array.from(s.value),r=z.findIndex(x=>x===f);if(~r)z.splice(r,1);else{if(e.accordion&&u.value.has(f)){const x=z.findIndex(M=>u.value.has(M));x>-1&&z.splice(x,1)}z.push(f)}G(z)}const E=f=>{const z=v.value.getPath(f??P.value,{includeSelf:!1}).keyPath;if(!z.length)return;const r=Array.from(s.value),x=new Set([...r,...z]);e.accordion&&u.value.forEach(M=>{x.has(M)&&!z.includes(M)&&x.delete(M)}),G(Array.from(x))},_=y(()=>{const{inverted:f}=e,{common:{cubicBezierEaseInOut:z},self:r}=a.value,{borderRadius:x,borderColorHorizontal:M,fontSize:no,itemHeight:lo,dividerColor:io}=r,n={"--n-divider-color":io,"--n-bezier":z,"--n-font-size":no,"--n-border-color-horizontal":M,"--n-border-radius":x,"--n-item-height":lo};return f?(n["--n-group-text-color"]=r.groupTextColorInverted,n["--n-color"]=r.colorInverted,n["--n-item-text-color"]=r.itemTextColorInverted,n["--n-item-text-color-hover"]=r.itemTextColorHoverInverted,n["--n-item-text-color-active"]=r.itemTextColorActiveInverted,n["--n-item-text-color-child-active"]=r.itemTextColorChildActiveInverted,n["--n-item-text-color-child-active-hover"]=r.itemTextColorChildActiveInverted,n["--n-item-text-color-active-hover"]=r.itemTextColorActiveHoverInverted,n["--n-item-icon-color"]=r.itemIconColorInverted,n["--n-item-icon-color-hover"]=r.itemIconColorHoverInverted,n["--n-item-icon-color-active"]=r.itemIconColorActiveInverted,n["--n-item-icon-color-active-hover"]=r.itemIconColorActiveHoverInverted,n["--n-item-icon-color-child-active"]=r.itemIconColorChildActiveInverted,n["--n-item-icon-color-child-active-hover"]=r.itemIconColorChildActiveHoverInverted,n["--n-item-icon-color-collapsed"]=r.itemIconColorCollapsedInverted,n["--n-item-text-color-horizontal"]=r.itemTextColorHorizontalInverted,n["--n-item-text-color-hover-horizontal"]=r.itemTextColorHoverHorizontalInverted,n["--n-item-text-color-active-horizontal"]=r.itemTextColorActiveHorizontalInverted,n["--n-item-text-color-child-active-horizontal"]=r.itemTextColorChildActiveHorizontalInverted,n["--n-item-text-color-child-active-hover-horizontal"]=r.itemTextColorChildActiveHoverHorizontalInverted,n["--n-item-text-color-active-hover-horizontal"]=r.itemTextColorActiveHoverHorizontalInverted,n["--n-item-icon-color-horizontal"]=r.itemIconColorHorizontalInverted,n["--n-item-icon-color-hover-horizontal"]=r.itemIconColorHoverHorizontalInverted,n["--n-item-icon-color-active-horizontal"]=r.itemIconColorActiveHorizontalInverted,n["--n-item-icon-color-active-hover-horizontal"]=r.itemIconColorActiveHoverHorizontalInverted,n["--n-item-icon-color-child-active-horizontal"]=r.itemIconColorChildActiveHorizontalInverted,n["--n-item-icon-color-child-active-hover-horizontal"]=r.itemIconColorChildActiveHoverHorizontalInverted,n["--n-arrow-color"]=r.arrowColorInverted,n["--n-arrow-color-hover"]=r.arrowColorHoverInverted,n["--n-arrow-color-active"]=r.arrowColorActiveInverted,n["--n-arrow-color-active-hover"]=r.arrowColorActiveHoverInverted,n["--n-arrow-color-child-active"]=r.arrowColorChildActiveInverted,n["--n-arrow-color-child-active-hover"]=r.arrowColorChildActiveHoverInverted,n["--n-item-color-hover"]=r.itemColorHoverInverted,n["--n-item-color-active"]=r.itemColorActiveInverted,n["--n-item-color-active-hover"]=r.itemColorActiveHoverInverted,n["--n-item-color-active-collapsed"]=r.itemColorActiveCollapsedInverted):(n["--n-group-text-color"]=r.groupTextColor,n["--n-color"]=r.color,n["--n-item-text-color"]=r.itemTextColor,n["--n-item-text-color-hover"]=r.itemTextColorHover,n["--n-item-text-color-active"]=r.itemTextColorActive,n["--n-item-text-color-child-active"]=r.itemTextColorChildActive,n["--n-item-text-color-child-active-hover"]=r.itemTextColorChildActiveHover,n["--n-item-text-color-active-hover"]=r.itemTextColorActiveHover,n["--n-item-icon-color"]=r.itemIconColor,n["--n-item-icon-color-hover"]=r.itemIconColorHover,n["--n-item-icon-color-active"]=r.itemIconColorActive,n["--n-item-icon-color-active-hover"]=r.itemIconColorActiveHover,n["--n-item-icon-color-child-active"]=r.itemIconColorChildActive,n["--n-item-icon-color-child-active-hover"]=r.itemIconColorChildActiveHover,n["--n-item-icon-color-collapsed"]=r.itemIconColorCollapsed,n["--n-item-text-color-horizontal"]=r.itemTextColorHorizontal,n["--n-item-text-color-hover-horizontal"]=r.itemTextColorHoverHorizontal,n["--n-item-text-color-active-horizontal"]=r.itemTextColorActiveHorizontal,n["--n-item-text-color-child-active-horizontal"]=r.itemTextColorChildActiveHorizontal,n["--n-item-text-color-child-active-hover-horizontal"]=r.itemTextColorChildActiveHoverHorizontal,n["--n-item-text-color-active-hover-horizontal"]=r.itemTextColorActiveHoverHorizontal,n["--n-item-icon-color-horizontal"]=r.itemIconColorHorizontal,n["--n-item-icon-color-hover-horizontal"]=r.itemIconColorHoverHorizontal,n["--n-item-icon-color-active-horizontal"]=r.itemIconColorActiveHorizontal,n["--n-item-icon-color-active-hover-horizontal"]=r.itemIconColorActiveHoverHorizontal,n["--n-item-icon-color-child-active-horizontal"]=r.itemIconColorChildActiveHorizontal,n["--n-item-icon-color-child-active-hover-horizontal"]=r.itemIconColorChildActiveHoverHorizontal,n["--n-arrow-color"]=r.arrowColor,n["--n-arrow-color-hover"]=r.arrowColorHover,n["--n-arrow-color-active"]=r.arrowColorActive,n["--n-arrow-color-active-hover"]=r.arrowColorActiveHover,n["--n-arrow-color-child-active"]=r.arrowColorChildActive,n["--n-arrow-color-child-active-hover"]=r.arrowColorChildActiveHover,n["--n-item-color-hover"]=r.itemColorHover,n["--n-item-color-active"]=r.itemColorActive,n["--n-item-color-active-hover"]=r.itemColorActiveHover,n["--n-item-color-active-collapsed"]=r.itemColorActiveCollapsed),n}),S=t?ue("menu",y(()=>e.inverted?"a":"b"),_,e):void 0,W=mo(),D=L(null),he=L(null);let F=!0;const Ne=()=>{var f;F?F=!1:(f=D.value)===null||f===void 0||f.sync({showAllItemsBeforeCalculate:!0})};function Ze(){return document.getElementById(W)}const ie=L(-1);function Je(f){ie.value=e.options.length-f}function Qe(f){f||(ie.value=-1)}const eo=y(()=>{const f=ie.value;return{children:f===-1?[]:e.options.slice(f)}}),oo=y(()=>{const{childrenField:f,disabledField:z,keyField:r}=e;return pe([eo.value],{getIgnored(x){return xe(x)},getChildren(x){return x[f]},getDisabled(x){return x[z]},getKey(x){var M;return(M=x[r])!==null&&M!==void 0?M:x.name}})}),to=y(()=>pe([{}]).treeNodes[0]);function ro(){var f;if(ie.value===-1)return h(ye,{root:!0,level:0,key:"__ellpisisGroupPlaceholder__",internalKey:"__ellpisisGroupPlaceholder__",title:"···",tmNode:to.value,domId:W,isEllipsisPlaceholder:!0});const z=oo.value.treeNodes[0],r=w.value,x=!!(!((f=z.children)===null||f===void 0)&&f.some(M=>r.includes(M.key)));return h(ye,{level:0,root:!0,key:"__ellpisisGroup__",internalKey:"__ellpisisGroup__",title:"···",virtualChildActive:x,tmNode:z,domId:W,rawNodes:z.rawNode.children||[],tmNodes:z.children||[],isEllipsisPlaceholder:!0})}return{mergedClsPrefix:o,controlledExpandedKeys:T,uncontrolledExpanededKeys:b,mergedExpandedKeys:s,uncontrolledValue:c,mergedValue:P,activePath:w,tmNodes:I,mergedTheme:a,mergedCollapsed:l,cssVars:t?void 0:_,themeClass:S==null?void 0:S.themeClass,overflowRef:D,counterRef:he,updateCounter:()=>{},onResize:Ne,onUpdateOverflow:Qe,onUpdateCount:Je,renderCounter:ro,getCounter:Ze,onRender:S==null?void 0:S.onRender,showOption:E,deriveResponsiveState:Ne}},render(){const{mergedClsPrefix:e,mode:o,themeClass:t,onRender:a}=this;a==null||a();const d=()=>this.tmNodes.map(i=>Te(i,this.$props)),v=o==="horizontal"&&this.responsive,u=()=>h("div",po(this.$attrs,{role:o==="horizontal"?"menubar":"menu",class:[`${e}-menu`,t,`${e}-menu--${o}`,v&&`${e}-menu--responsive`,this.mergedCollapsed&&`${e}-menu--collapsed`],style:this.cssVars}),v?h(Po,{ref:"overflowRef",onUpdateOverflow:this.onUpdateOverflow,getCounter:this.getCounter,onUpdateCount:this.onUpdateCount,updateCounter:this.updateCounter,style:{width:"100%",display:"flex",overflow:"hidden"}},{default:d,counter:this.renderCounter}):d());return v?h(ho,{onResize:this.onResize},{default:u}):u()}}),tt=$({__name:"AppNav",emits:["navigate"],setup(e,{emit:o}){const t=o,a=we(),d=je(),{t:l}=ze(),v={home:'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',autoReverse:'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>',config:'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',browserTask:'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>',setting:'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>'};function u(C){return()=>h("div",{class:"app-nav__option"},[h("div",{class:"app-nav__option-head"},[h("span",{class:"app-nav__option-label"},C.label)])])}function i(C){return()=>h("span",{class:"app-nav__icon-svg",innerHTML:C})}function c(C){return{key:C.to,label:u(C),icon:i(C.iconSvg)}}const A=y(()=>[{type:"group",key:"group-overview",label:l("nav.groups.overview"),children:[c({label:l("nav.items.home.label"),to:B.HOME,iconSvg:v.home})]},{type:"group",key:"group-tasks",label:l("nav.groups.tasks"),children:[c({label:l("nav.items.autoReverse.label"),to:B.AUTO_REVERSE,iconSvg:v.autoReverse}),c({label:l("nav.items.config.label"),to:B.AUTO_REVERSE_CONFIG,iconSvg:v.config}),c({label:l("nav.items.browserTask.label"),to:B.BROWSER_TASK,iconSvg:v.browserTask})]},{type:"group",key:"group-system",label:l("nav.groups.system"),children:[c({label:l("nav.items.setting.label"),to:B.SETTING,iconSvg:v.setting})]}]),P=y(()=>[B.HOME,B.AUTO_REVERSE,B.AUTO_REVERSE_CONFIG,B.BROWSER_TASK,B.SETTING].find(T=>a.path===T||a.path.startsWith(`${T}/`))??B.HOME),b=async C=>{if(C===a.path){t("navigate");return}await d.push(C),t("navigate")};return(C,T)=>(O(),se(N(ot),{value:P.value,options:A.value,indent:18,class:"app-nav","onUpdate:value":b},null,8,["value","options"]))}}),Xe=ve(tt,[["__scopeId","data-v-f37720a0"]]),rt={key:0,class:"mobile-bottom-nav","aria-label":"Primary"},nt={class:"mobile-bottom-nav__inner"},lt=["onClick"],it={class:"mobile-bottom-nav__icon"},at={key:0,xmlns:"http://www.w3.org/2000/svg",width:"22",height:"22",viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},st={key:1,xmlns:"http://www.w3.org/2000/svg",width:"22",height:"22",viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},ct={key:2,xmlns:"http://www.w3.org/2000/svg",width:"22",height:"22",viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},dt={key:3,xmlns:"http://www.w3.org/2000/svg",width:"22",height:"22",viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},ut={key:4,xmlns:"http://www.w3.org/2000/svg",width:"22",height:"22",viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},vt={key:5,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round"},ht={class:"mobile-bottom-nav__label"},mt=$({__name:"MobileBottomNav",props:{isMobile:{type:Boolean}},setup(e){const o=we(),t=je(),{t:a}=ze(),d=y(()=>[{key:"home",label:a("nav.items.home.label"),path:B.HOME},{key:"auto",label:a("nav.items.autoReverse.label"),path:B.AUTO_REVERSE},{key:"tasks",label:a("nav.items.browserTask.label"),path:B.BROWSER_TASK},{key:"config",label:a("nav.items.config.label"),path:B.AUTO_REVERSE_CONFIG},{key:"settings",label:a("nav.items.setting.label"),path:B.SETTING}]),l=u=>o.path===u||o.path.startsWith(u+"/"),v=u=>{o.path!==u&&t.push(u)};return(u,i)=>e.isMobile?(O(),H("nav",rt,[m("div",nt,[(O(!0),H(Fe,null,fo(d.value,c=>(O(),H("button",{key:c.path,type:"button",class:te(["mobile-bottom-nav__item",{"mobile-bottom-nav__item--active":l(c.path)}]),onClick:A=>v(c.path)},[m("div",it,[c.key==="home"?(O(),H("svg",at,[...i[0]||(i[0]=[m("rect",{width:"7",height:"9",x:"3",y:"3",rx:"1"},null,-1),m("rect",{width:"7",height:"5",x:"14",y:"3",rx:"1"},null,-1),m("rect",{width:"7",height:"9",x:"14",y:"12",rx:"1"},null,-1),m("rect",{width:"7",height:"5",x:"3",y:"16",rx:"1"},null,-1)])])):c.key==="auto"?(O(),H("svg",st,[...i[1]||(i[1]=[Ae('<rect width="16" height="16" x="4" y="4" rx="2" data-v-5210f495></rect><rect width="6" height="6" x="9" y="9" rx="1" data-v-5210f495></rect><path d="M15 2v2" data-v-5210f495></path><path d="M15 20v2" data-v-5210f495></path><path d="M2 15h2" data-v-5210f495></path><path d="M2 9h2" data-v-5210f495></path><path d="M20 15h2" data-v-5210f495></path><path d="M20 9h2" data-v-5210f495></path><path d="M9 2v2" data-v-5210f495></path><path d="M9 20v2" data-v-5210f495></path>',10)])])):c.key==="tasks"?(O(),H("svg",ct,[...i[2]||(i[2]=[Ae('<path d="M12 8V4H8" data-v-5210f495></path><rect width="16" height="12" x="4" y="8" rx="2" data-v-5210f495></rect><path d="M2 14h2" data-v-5210f495></path><path d="M20 14h2" data-v-5210f495></path><path d="M15 13v2" data-v-5210f495></path><path d="M9 13v2" data-v-5210f495></path>',6)])])):c.key==="config"?(O(),H("svg",dt,[...i[3]||(i[3]=[m("path",{d:"M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"},null,-1),m("circle",{cx:"12",cy:"12",r:"3"},null,-1)])])):c.key==="settings"?(O(),H("svg",ut,[...i[4]||(i[4]=[m("path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"},null,-1)])])):(O(),H("svg",vt,[...i[5]||(i[5]=[m("circle",{cx:"12",cy:"12",r:"10"},null,-1)])]))]),m("span",ht,q(c.label),1)],10,lt))),128))])])):re("",!0)}}),pt=ve(mt,[["__scopeId","data-v-5210f495"]]),gt={class:"sidebar-content"},ft={class:"sidebar-nav-container"},bt=$({__name:"SidebarContent",emits:["navigate"],setup(e){return(o,t)=>(O(),H("div",gt,[m("div",ft,[V(Xe,{onNavigate:t[0]||(t[0]=a=>o.$emit("navigate"))})])]))}}),xt=ve(bt,[["__scopeId","data-v-161976c8"]]),yt={key:0,class:"main-layout__brand-copy"},Ct=["aria-label"],wt={key:0,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2",width:"16",height:"16"},zt={key:1,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2",width:"16",height:"16"},_t={class:"main-layout__header-left"},St=["aria-label"],kt={class:"main-layout__page-meta"},It={class:"main-layout__eyebrow"},Rt={class:"main-layout__header-actions"},Tt=["aria-label"],Nt={class:"main-layout__locale"},Pt=["aria-label"],Mt={key:0,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2",width:"18",height:"18"},At={key:1,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2",width:"18",height:"18"},Et={class:"main-layout__avatar"},Bt={class:"main-layout__content-inner"},Ot={class:"main-layout__drawer-header"},Ht={class:"main-layout__brand-copy"},$t={class:"main-layout__drawer-body"},Lt={class:"main-layout__drawer-footer"},Ft=$({__name:"MainLayout",setup(e){const{t:o,locale:t,setLocale:a}=ze(),{isLightMode:d,toggleTheme:l}=_o(),v=we(),u=L(!1),i=L(!1),c=L(!1),A=y(()=>({[B.HOME]:o("nav.items.home.label"),[B.AUTO_REVERSE]:o("nav.items.autoReverse.label"),[B.AUTO_REVERSE_CONFIG]:o("nav.items.config.label"),[B.BROWSER_TASK]:o("nav.items.browserTask.label"),[B.SETTING]:o("nav.items.setting.label")})),P=y(()=>{const s=Object.keys(A.value).find(I=>v.path===I||v.path.startsWith(`${I}/`));return s?A.value[s]:o("nav.items.home.label")});function b(){typeof window>"u"||(c.value=window.innerWidth<960,c.value||(i.value=!1))}function C(){a(t.value==="zh-CN"?"en-US":"zh-CN")}return bo(()=>{b(),window.addEventListener("resize",b)}),xo(()=>{window.removeEventListener("resize",b)}),(T,s)=>{const I=So("router-view");return O(),se(N(Ee),{class:te(["main-layout",{"is-mobile":c.value}]),"has-sider":""},{default:j(()=>[c.value?re("",!0):(O(),se(N(Do),{key:0,"collapse-mode":"width","collapsed-width":76,width:228,collapsed:u.value,bordered:"","show-trigger":"arrow-circle",class:"main-layout__sider",onCollapse:s[1]||(s[1]=w=>u.value=!0),onExpand:s[2]||(s[2]=w=>u.value=!1)},{default:j(()=>[m("div",{class:te(["main-layout__brand",{"is-collapsed":u.value}])},[s[8]||(s[8]=m("div",{class:"main-layout__brand-mark"},[m("svg",{viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},[m("polygon",{points:"12 2 2 7 12 12 22 7 12 2"}),m("polyline",{points:"2 17 12 22 22 17"}),m("polyline",{points:"2 12 12 17 22 12"})])],-1)),u.value?re("",!0):(O(),H("div",yt,[s[7]||(s[7]=m("strong",null,"AutoReverse",-1)),m("span",null,q(N(o)("nav.groups.tasks")),1)]))],2),m("div",{class:te(["main-layout__nav",{"main-layout__nav--collapsed":u.value}])},[V(Xe)],2),m("div",{class:te(["main-layout__sider-footer",{"is-collapsed":u.value}])},[m("button",{type:"button",class:"main-layout__action-pill",onClick:s[0]||(s[0]=(...w)=>N(l)&&N(l)(...w)),"aria-label":N(o)("setting.fields.themeLabel")},[N(d)?(O(),H("svg",wt,[...s[9]||(s[9]=[m("path",{d:"M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-11.314l.707.707m11.314 11.314l.707.707M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"},null,-1)])])):(O(),H("svg",zt,[...s[10]||(s[10]=[m("path",{d:"M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"},null,-1)])]))],8,Ct)],2)]),_:1},8,["collapsed"])),V(N(Ee),{class:"main-layout__shell"},{default:j(()=>[V(N(Fo),{bordered:"",class:"main-layout__header"},{default:j(()=>[m("div",_t,[c.value?(O(),H("button",{key:0,type:"button",class:"main-layout__header-btn","aria-label":N(o)("nav.aria"),onClick:s[3]||(s[3]=w=>i.value=!0)},[...s[11]||(s[11]=[m("svg",{viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2",width:"18",height:"18"},[m("path",{d:"M3 12h18M3 6h18M3 18h18"})],-1)])],8,St)):re("",!0),m("div",kt,[m("span",It,q(c.value?"Workspace":N(o)("nav.groups.overview")),1),m("strong",null,q(P.value),1)])]),m("div",Rt,[m("button",{type:"button",class:"main-layout__header-btn",onClick:C,"aria-label":N(o)("setting.fields.localeLabel")},[m("span",Nt,q(N(t)==="zh-CN"?"EN":"中"),1)],8,Tt),c.value?(O(),H("button",{key:0,type:"button",class:"main-layout__header-btn",onClick:s[4]||(s[4]=(...w)=>N(l)&&N(l)(...w)),"aria-label":N(o)("setting.fields.themeLabel")},[N(d)?(O(),H("svg",Mt,[...s[12]||(s[12]=[m("path",{d:"M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-11.314l.707.707m11.314 11.314l.707.707M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"},null,-1)])])):(O(),H("svg",At,[...s[13]||(s[13]=[m("path",{d:"M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"},null,-1)])]))],8,Pt)):re("",!0),m("div",Et,q(P.value.slice(0,1)),1)])]),_:1}),V(N(Ho),{class:"main-layout__content"},{default:j(()=>[m("div",Bt,[V(I,null,{default:j(({Component:w})=>[V(yo,{name:"fade-slide",mode:"out-in"},{default:j(()=>[(O(),se(Co(w)))]),_:2},1024)]),_:1})])]),_:1})]),_:1}),V(pt,{"is-mobile":c.value},null,8,["is-mobile"]),V(N(Ro),{show:i.value,"onUpdate:show":s[6]||(s[6]=w=>i.value=w),placement:"left",width:300},{default:j(()=>[V(N(Io),{"native-scrollbar":!1,closable:""},{header:j(()=>[m("div",Ot,[s[15]||(s[15]=m("div",{class:"main-layout__brand-mark main-layout__brand-mark--small"},[m("svg",{viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":"2","stroke-linecap":"round","stroke-linejoin":"round"},[m("polygon",{points:"12 2 2 7 12 12 22 7 12 2"}),m("polyline",{points:"2 17 12 22 22 17"}),m("polyline",{points:"2 12 12 17 22 12"})])],-1)),m("div",Ht,[s[14]||(s[14]=m("strong",null,"AutoReverse",-1)),m("span",null,q(N(o)("nav.groups.tasks")),1)])])]),footer:j(()=>[m("div",Lt,[V(N(wo),{quaternary:"",block:"",onClick:C},{default:j(()=>[zo(q(N(t)==="zh-CN"?"English":"中文"),1)]),_:1})])]),default:j(()=>[m("div",$t,[V(xt,{onNavigate:s[5]||(s[5]=w=>i.value=!1)})])]),_:1})]),_:1},8,["show"])]),_:1},8,["class"])}}}),qt=ve(Ft,[["__scopeId","data-v-ee2e7a68"]]);export{qt as default};
